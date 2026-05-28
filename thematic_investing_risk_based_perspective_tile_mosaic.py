#!/usr/bin/env python
# coding: utf-8

# # Thematic Investing: tile-based Mosaic + bootstrap 実装
# 
# このNotebookは、APWC z-score `> 2` を実運用シグナルへ応用する前段として、公開済みテーマ構成銘柄だけを使う live/post-release 設計で実装しています。
# 
# 主な変更点は次の通りです。
# 
# - Mosaic + bootstrap を、時間バッチ × 銘柄パネルの tile-based residualization に置き換える。
# - 各tile内で日次クロスセクション回帰を行い、bootstrapサンプルも同じtileのQR射影で再残差化する。
# - bootstrapごとの `np.linalg.lstsq` 再実行をやめ、QR基底をキャッシュしてchunk単位でベクトル化する。
# - リリース日前後分析は実装しない。特徴量は分析日 `t` まで、評価ラベルは `t+1` 以降のみ。
# - リターン持続性は、Mosaic + bootstrap APWC z-score `>= 2` 群と `< 2` 群に分け、バスケット残差リターンで検証する。
# 
# Barraファクター回帰による戦略実証はこのNotebookの対象外です。ここでは、残差推定に必要なファクターエクスポージャーのみを使います。

# ## 0. 設定と依存ライブラリ

# In[1]:


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm
from IPython.display import display

pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 180)
pd.set_option("display.float_format", lambda x: f"{x:,.6f}")

PROJECT_ROOT = Path.cwd()
DATA_RAW = PROJECT_ROOT / "data" / "raw"

@dataclass(frozen=True)
class Config:
    seed: int = 42
    window: int = 60
    future_window: int = 60
    mosaic_batch_size: int = 10
    mosaic_panel_min_factor_multiplier: int = 5
    bootstrap_reps_synthetic: int = 500
    bootstrap_reps_real: int = 1000
    bootstrap_chunk_size: int = 64
    min_obs_ratio: float = 0.80
    z_threshold: float = 2.0
    trading_days_per_year: int = 252
    max_analysis_dates_per_theme: int = 3
    min_members: int = 2
    rank_tol: float = 1e-10

cfg = Config()
print(cfg)


# ## 1. 入力スキーマ
# 
# 実データを使う場合は、以下の4テーブルを `data/raw/` に `.parquet` または `.csv` で配置します。どれか一部だけ存在する状態は、混在を避けるためエラーにします。

# In[2]:


REQUIRED_SCHEMAS: dict[str, set[str]] = {
    "theme_constituents": {"as_of_date", "theme_id", "theme_name", "release_date", "ticker", "weight"},
    "stock_total_returns": {"date", "ticker", "total_return"},
    "barra_gemltl_exposures": {"date", "ticker", "factor", "exposure"},
    "universe": {"date", "ticker", "in_universe"},
}

DATE_COLUMNS = {
    "theme_constituents": ["as_of_date", "release_date"],
    "stock_total_returns": ["date"],
    "barra_gemltl_exposures": ["date"],
    "universe": ["date"],
}

NUMERIC_COLUMNS = {
    "theme_constituents": ["weight"],
    "stock_total_returns": ["total_return"],
    "barra_gemltl_exposures": ["exposure"],
    "universe": [],
}


def find_table(stem: str) -> Path | None:
    for suffix in (".parquet", ".csv"):
        candidate = DATA_RAW / f"{stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported table format: {path}")


def validate_schema(name: str, df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_SCHEMAS[name] - set(df.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")

    out = df.copy()
    for col in DATE_COLUMNS[name]:
        out[col] = pd.to_datetime(out[col])
    for col in NUMERIC_COLUMNS[name]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if name == "universe":
        out["in_universe"] = out["in_universe"].astype(bool)
    return out


def validate_all_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {name: validate_schema(name, df) for name, df in tables.items()}

schema_table = pd.DataFrame(
    [(name, sorted(cols)) for name, cols in REQUIRED_SCHEMAS.items()],
    columns=["table", "required_columns"],
)
display(schema_table)


# ## 2. データロードまたは合成データ生成
# 
# 実データ未配置時は、同じスキーマの合成データでsmoke testを行います。合成データは、coherent theme と non-coherent theme の検出処理を検査するためのもので、研究結果として解釈しません。

# In[3]:


def generate_synthetic_tables(cfg: Config) -> dict[str, pd.DataFrame]:
    local_rng = np.random.default_rng(cfg.seed)
    dates = pd.bdate_range("2022-01-04", periods=430)
    tickers = [f"JP{i:04d}" for i in range(1, 181)]
    factors = ["market", "value", "size", "momentum", "quality"]

    static_exposure = pd.DataFrame(
        local_rng.normal(0.0, 1.0, size=(len(tickers), len(factors))),
        index=tickers,
        columns=factors,
    )
    # Interceptと完全共線にならないよう、market exposureは1近辺のクロスセクション差を持たせる。
    static_exposure["market"] = 1.0 + local_rng.normal(0.0, 0.20, size=len(tickers))

    exposure_frames = []
    for date in dates:
        exp = static_exposure + local_rng.normal(0.0, 0.015, size=static_exposure.shape)
        frame = (
            exp.reset_index()
            .melt(id_vars="index", var_name="factor", value_name="exposure")
            .rename(columns={"index": "ticker"})
        )
        frame.insert(0, "date", date)
        exposure_frames.append(frame)
    barra_gemltl_exposures = pd.concat(exposure_frames, ignore_index=True)

    factor_returns = pd.DataFrame(
        local_rng.normal(0.0, 0.003, size=(len(dates), len(factors))),
        index=dates,
        columns=factors,
    )
    factor_returns["market"] = local_rng.normal(0.0002, 0.006, size=len(dates))

    theme_specs = {
        "T001": {
            "theme_name": "Synthetic Coherent AI Infrastructure",
            "members": tickers[:35],
            "release_idx": 70,
            "common_scale": 0.025,
        },
        "T002": {
            "theme_name": "Synthetic Moderate Green Transition",
            "members": tickers[40:75],
            "release_idx": 95,
            "common_scale": 0.008,
        },
        "T003": {
            "theme_name": "Synthetic Non Coherent Domestic Demand",
            "members": tickers[110:145],
            "release_idx": 285,
            "common_scale": 0.000,
        },
    }

    common_shocks: dict[str, np.ndarray] = {}
    event_start, event_end = 70, 245
    for theme_id, spec in theme_specs.items():
        shock = np.zeros(len(dates))
        for t in range(1, len(dates)):
            innovation_scale = spec["common_scale"] if event_start <= t <= event_end else spec["common_scale"] * 0.10
            shock[t] = 0.65 * shock[t - 1] + local_rng.normal(0.0, innovation_scale)
        common_shocks[theme_id] = shock

    return_frames = []
    for t, date in enumerate(dates):
        exp_today = barra_gemltl_exposures[barra_gemltl_exposures["date"].eq(date)].pivot(
            index="ticker", columns="factor", values="exposure"
        )[factors]
        systematic = exp_today.to_numpy() @ factor_returns.loc[date, factors].to_numpy()
        residual = local_rng.normal(0.0, 0.008, size=len(tickers))
        for theme_id, spec in theme_specs.items():
            member_idx = [tickers.index(x) for x in spec["members"]]
            residual[member_idx] += common_shocks[theme_id][t]
        total_return = systematic + residual
        return_frames.append(pd.DataFrame({"date": date, "ticker": tickers, "total_return": total_return}))
    stock_total_returns = pd.concat(return_frames, ignore_index=True)

    constituent_rows = []
    for theme_id, spec in theme_specs.items():
        release_date = dates[spec["release_idx"]]
        weight = 1.0 / len(spec["members"])
        for ticker in spec["members"]:
            constituent_rows.append((release_date, theme_id, spec["theme_name"], release_date, ticker, weight))
    theme_constituents = pd.DataFrame(
        constituent_rows,
        columns=["as_of_date", "theme_id", "theme_name", "release_date", "ticker", "weight"],
    )

    universe = pd.MultiIndex.from_product([dates, tickers], names=["date", "ticker"]).to_frame(index=False)
    universe["in_universe"] = True

    return {
        "theme_constituents": theme_constituents,
        "stock_total_returns": stock_total_returns,
        "barra_gemltl_exposures": barra_gemltl_exposures,
        "universe": universe,
    }


def load_or_generate_tables(cfg: Config) -> tuple[dict[str, pd.DataFrame], bool, dict[str, Path | None]]:
    paths = {name: find_table(name) for name in REQUIRED_SCHEMAS}
    present = {name: path for name, path in paths.items() if path is not None}
    if len(present) == len(REQUIRED_SCHEMAS):
        tables = {name: read_table(path) for name, path in present.items()}
        return validate_all_tables(tables), False, paths
    if len(present) == 0:
        tables = generate_synthetic_tables(cfg)
        return validate_all_tables(tables), True, paths
    missing = sorted(set(REQUIRED_SCHEMAS) - set(present))
    raise FileNotFoundError(
        "実データを使う場合は4テーブルをすべて配置してください。"
        f" present={sorted(present)}, missing={missing}, data_dir={DATA_RAW}"
    )


tables, USING_SYNTHETIC_DATA, input_paths = load_or_generate_tables(cfg)
print(f"USING_SYNTHETIC_DATA = {USING_SYNTHETIC_DATA}")
print(f"DATA_RAW = {DATA_RAW}")
display(pd.DataFrame({"table": list(input_paths), "path": [str(v) if v else None for v in input_paths.values()]}))
display(pd.DataFrame({name: [df.shape[0], df.shape[1]] for name, df in tables.items()}, index=["rows", "cols"]).T)


# In[4]:


theme_constituents = tables["theme_constituents"]
stock_total_returns = tables["stock_total_returns"]
barra_gemltl_exposures = tables["barra_gemltl_exposures"]
universe = tables["universe"]

schema_checks = []
for name, df in tables.items():
    schema_checks.append(
        {
            "table": name,
            "rows": len(df),
            "unique_dates": df["date"].nunique() if "date" in df.columns else df["as_of_date"].nunique(),
            "unique_tickers": df["ticker"].nunique() if "ticker" in df.columns else None,
            "missing_cells": int(df.isna().sum().sum()),
        }
    )

schema_checks = pd.DataFrame(schema_checks)
display(schema_checks)

assert set(theme_constituents["ticker"]).issubset(set(stock_total_returns["ticker"])), "テーマ構成銘柄がリターンに存在しません。"
assert set(stock_total_returns["ticker"]).intersection(set(barra_gemltl_exposures["ticker"])), "リターンとエクスポージャーに共通銘柄がありません。"


# ## 3. 通常のクロスセクション回帰による残差リターン
# 
# この残差は、過去・将来のバスケット残差リターン、リスク過小評価、持続性分析に使います。APWC z-score の統計的有意性は、次章のtile-based Mosaic + bootstrapで別途評価します。

# In[5]:


def build_exposure_lookup(
    exposures: pd.DataFrame,
    universe: pd.DataFrame,
) -> tuple[dict[pd.Timestamp, pd.DataFrame], dict[pd.Timestamp, set[str]], list[str]]:
    factor_names = sorted(exposures["factor"].unique())
    exposure_by_date = {
        date: g.pivot(index="ticker", columns="factor", values="exposure").reindex(columns=factor_names)
        for date, g in exposures.groupby("date", sort=True)
    }
    universe_by_date = {
        date: set(g.loc[g["in_universe"], "ticker"])
        for date, g in universe.groupby("date", sort=True)
    }
    return exposure_by_date, universe_by_date, factor_names


def fit_residual_wide_from_returns_wide(
    returns_wide: pd.DataFrame,
    exposure_by_date: dict[pd.Timestamp, pd.DataFrame],
    universe_by_date: dict[pd.Timestamp, set[str]],
    factor_names: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    residual_wide = pd.DataFrame(index=returns_wide.index, columns=returns_wide.columns, dtype=float)
    beta_rows: list[dict[str, Any]] = []
    diag_rows: list[dict[str, Any]] = []

    for date in returns_wide.index:
        y_all = returns_wide.loc[date].dropna()
        exposures = exposure_by_date.get(date)
        universe_set = universe_by_date.get(date, set(y_all.index))
        if exposures is None:
            continue

        tickers = y_all.index.intersection(exposures.dropna().index)
        tickers = [ticker for ticker in tickers if ticker in universe_set]
        if len(tickers) <= len(factor_names) + 1:
            diag_rows.append({"date": date, "n_obs": len(tickers), "status": "too_few_obs"})
            continue

        y = y_all.loc[tickers].astype(float).to_numpy()
        x_factor = exposures.loc[tickers, factor_names].astype(float).to_numpy()
        x = np.column_stack([np.ones(len(tickers)), x_factor])
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        fitted = x @ beta
        residual = y - fitted
        residual_wide.loc[date, tickers] = residual

        row = {"date": date, "intercept": beta[0]}
        row.update({factor: beta[i + 1] for i, factor in enumerate(factor_names)})
        beta_rows.append(row)
        diag_rows.append(
            {
                "date": date,
                "n_obs": len(tickers),
                "n_factors": len(factor_names),
                "design_rank": int(np.linalg.matrix_rank(x)),
                "residual_mean": float(np.mean(residual)),
                "residual_std": float(np.std(residual, ddof=1)),
                "status": "ok",
            }
        )

    factor_returns = pd.DataFrame(beta_rows).set_index("date").sort_index()
    diagnostics = pd.DataFrame(diag_rows).sort_values("date")
    return residual_wide, factor_returns, diagnostics


returns_wide = stock_total_returns.pivot(index="date", columns="ticker", values="total_return").sort_index()
exposure_by_date, universe_by_date, factor_names = build_exposure_lookup(barra_gemltl_exposures, universe)
residuals_wide, factor_returns, regression_diagnostics = fit_residual_wide_from_returns_wide(
    returns_wide, exposure_by_date, universe_by_date, factor_names
)

ok_diag = regression_diagnostics[regression_diagnostics["status"].eq("ok")]
max_abs_residual_mean = ok_diag["residual_mean"].abs().max()
print(f"factors = {factor_names}")
print(f"regression dates ok = {len(ok_diag)} / {len(regression_diagnostics)}")
print(f"max abs daily residual mean = {max_abs_residual_mean:.3e}")
assert max_abs_residual_mean < 1e-10, "OLS残差の日次平均が十分にゼロではありません。"
display(ok_diag.tail())


# ## 4. tile-based Mosaic + bootstrap
# 
# 実装上の要点は次の通りです。
# 
# 1. 分析窓を10営業日バッチに分割する。
# 2. 各バッチ内で、銘柄をランダムな非重複パネルへ分割する。各パネルは原則として `5 × 回帰説明変数数` 以上の銘柄を持つようにする。
# 3. 各 `日付 × 銘柄パネル` のtile内で、日次クロスセクション回帰を行い、QR基底を保存する。
# 4. bootstrapでは、tileパネル単位で10日ブロックを再標本化し、保存済みQR基底で再残差化する。
# 5. basket内のtile残差からAPWCを再計算し、帰無分布の平均・標準偏差からz-scoreを作る。
# 
# この設計により、bootstrap replicateごとのフルユニバース回帰再実行を避けます。

# In[6]:


def latest_constituents(
    constituents: pd.DataFrame,
    theme_id: str,
    analysis_date: pd.Timestamp,
    public_only: bool = True,
) -> pd.DataFrame:
    df = constituents[constituents["theme_id"].eq(theme_id)].copy()
    df = df[df["as_of_date"].le(analysis_date)]
    if public_only:
        df = df[df["release_date"].le(analysis_date)]
    if df.empty:
        return df
    latest_as_of = df["as_of_date"].max()
    df = df[df["as_of_date"].eq(latest_as_of)].copy()
    weight_sum = df["weight"].sum()
    if not np.isfinite(weight_sum) or abs(weight_sum) < 1e-12:
        df["weight"] = 1.0 / len(df)
    else:
        df["weight"] = df["weight"] / weight_sum
    return df


def basket_residual_return(residual_window: pd.DataFrame, constituent_df: pd.DataFrame) -> pd.Series:
    tickers = [ticker for ticker in constituent_df["ticker"] if ticker in residual_window.columns]
    if len(tickers) == 0:
        return pd.Series(index=residual_window.index, dtype=float)
    weights = constituent_df.set_index("ticker").loc[tickers, "weight"].astype(float)
    weights = weights / weights.sum()
    return residual_window[tickers].mul(weights, axis=1).sum(axis=1, min_count=1)


def average_pairwise_corr_array(values: np.ndarray, min_obs_ratio: float = cfg.min_obs_ratio) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 2 or arr.shape[1] < 2 or arr.shape[0] < 3:
        return np.nan
    min_obs = int(np.ceil(arr.shape[0] * min_obs_ratio))
    counts = np.isfinite(arr).sum(axis=0)
    arr = arr[:, counts >= min_obs]
    if arr.shape[1] < 2:
        return np.nan

    if not np.isfinite(arr).all():
        corr = pd.DataFrame(arr).corr(min_periods=min_obs).to_numpy(dtype=float)
        upper = corr[np.triu_indices_from(corr, k=1)]
        upper = upper[np.isfinite(upper)]
        return float(np.mean(upper)) if upper.size else np.nan

    centered = arr - arr.mean(axis=0, keepdims=True)
    std = centered.std(axis=0, ddof=1)
    good = np.isfinite(std) & (std > 0)
    z = centered[:, good] / std[good]
    n = z.shape[1]
    if n < 2:
        return np.nan
    row_sum = z.sum(axis=1)
    sum_upper_corr = (row_sum @ row_sum - np.sum(z * z)) / (2.0 * (z.shape[0] - 1))
    return float(sum_upper_corr / (n * (n - 1) / 2.0))


def average_pairwise_corr_many(values: np.ndarray, min_obs_ratio: float = cfg.min_obs_ratio) -> np.ndarray:
    vals = np.asarray(values, dtype=float)
    if vals.ndim != 3:
        raise ValueError("values must have shape (n_reps, n_dates, n_tickers)")
    n_reps, n_dates, n_tickers = vals.shape
    out = np.full(n_reps, np.nan, dtype=float)
    if n_dates < 3 or n_tickers < 2:
        return out

    if np.isfinite(vals).all():
        centered = vals - vals.mean(axis=1, keepdims=True)
        std = centered.std(axis=1, ddof=1)
        good = np.isfinite(std) & (std > 0)
        for i in range(n_reps):
            g = good[i]
            n = int(g.sum())
            if n < 2:
                continue
            z = centered[i][:, g] / std[i, g]
            row_sum = z.sum(axis=1)
            sum_upper_corr = (row_sum @ row_sum - np.sum(z * z)) / (2.0 * (n_dates - 1))
            out[i] = sum_upper_corr / (n * (n - 1) / 2.0)
        return out

    for i in range(n_reps):
        out[i] = average_pairwise_corr_array(vals[i], min_obs_ratio=min_obs_ratio)
    return out


def average_pairwise_corr(window: pd.DataFrame, min_obs_ratio: float = cfg.min_obs_ratio) -> float:
    return average_pairwise_corr_array(window.to_numpy(dtype=float), min_obs_ratio=min_obs_ratio)


# In[7]:


@dataclass
class TileProjection:
    batch_id: int
    panel_id: int
    date_pos: int
    ticker_pos: np.ndarray
    x: np.ndarray
    q: np.ndarray


@dataclass
class MosaicWorkspace:
    dates: pd.Index
    tickers: pd.Index
    time_batches: list[np.ndarray]
    panels_by_batch: list[list[np.ndarray]]
    projections: list[TileProjection]
    residual_array: np.ndarray
    diagnostics: dict[str, Any]


def make_time_batches(n_dates: int, batch_size: int) -> list[np.ndarray]:
    return [np.arange(start, min(start + batch_size, n_dates), dtype=int) for start in range(0, n_dates, batch_size)]


def make_equal_stock_panels(
    n_tickers: int,
    n_regressors: int,
    cfg: Config,
    rng: np.random.Generator,
) -> list[np.ndarray]:
    min_panel_size = max(2, cfg.mosaic_panel_min_factor_multiplier * n_regressors)
    n_panels = max(1, n_tickers // min_panel_size)
    order = np.arange(n_tickers, dtype=int)
    rng.shuffle(order)
    return [np.asarray(panel, dtype=int) for panel in np.array_split(order, n_panels) if len(panel) > 0]


def orthonormal_basis(x: np.ndarray, tol: float = cfg.rank_tol) -> np.ndarray:
    if x.ndim != 2 or x.shape[0] == 0 or x.shape[1] == 0:
        return np.empty((x.shape[0], 0), dtype=float)
    q, r = np.linalg.qr(x, mode="reduced")
    diag = np.abs(np.diag(r))
    if diag.size == 0:
        return np.empty((x.shape[0], 0), dtype=float)
    threshold = tol * max(x.shape) * max(float(diag.max()), 1.0)
    rank = int(np.sum(diag > threshold))
    return q[:, :rank]


def residualize_vector_with_q(y: np.ndarray, q: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if q.size == 0:
        return y.copy()
    return y - q @ (q.T @ y)


def residualize_matrix_with_q(y: np.ndarray, q: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    if q.size == 0:
        return y.copy()
    return y - (y @ q) @ q.T


def build_mosaic_workspace(
    returns_wide: pd.DataFrame,
    exposure_by_date: dict[pd.Timestamp, pd.DataFrame],
    universe_by_date: dict[pd.Timestamp, set[str]],
    factor_names: list[str],
    dates: pd.Index,
    cfg: Config,
    seed: int,
) -> MosaicWorkspace:
    rng = np.random.default_rng(seed)
    dates = pd.Index(pd.to_datetime(dates))
    tickers = pd.Index(returns_wide.columns)
    ticker_to_pos = {ticker: i for i, ticker in enumerate(tickers)}
    n_dates = len(dates)
    n_tickers = len(tickers)
    n_regressors = len(factor_names) + 1

    time_batches = make_time_batches(n_dates, cfg.mosaic_batch_size)
    panels_by_batch = [make_equal_stock_panels(n_tickers, n_regressors, cfg, rng) for _ in time_batches]

    residual_array = np.full((n_dates, n_tickers), np.nan, dtype=float)
    projections: list[TileProjection] = []
    ranks: list[int] = []
    panel_sizes: list[int] = []
    skipped_projections = 0

    for batch_id, batch in enumerate(time_batches):
        for panel_id, panel_pos in enumerate(panels_by_batch[batch_id]):
            panel_sizes.append(len(panel_pos))
            panel_tickers = tickers[panel_pos]
            for date_pos in batch:
                date = pd.Timestamp(dates[date_pos])
                y_row = returns_wide.loc[date]
                exposures = exposure_by_date.get(date)
                if exposures is None:
                    skipped_projections += 1
                    continue
                universe_set = universe_by_date.get(date, set(panel_tickers))

                candidate_tickers = [
                    ticker for ticker in panel_tickers
                    if ticker in universe_set and ticker in exposures.index and pd.notna(y_row.get(ticker, np.nan))
                ]
                if not candidate_tickers:
                    skipped_projections += 1
                    continue
                x_df = exposures.reindex(candidate_tickers)[factor_names]
                y_series = y_row.reindex(candidate_tickers).astype(float)
                valid = x_df.notna().all(axis=1) & y_series.notna()
                valid_tickers = list(x_df.index[valid])
                if len(valid_tickers) <= n_regressors + 1:
                    skipped_projections += 1
                    continue

                ticker_pos = np.asarray([ticker_to_pos[ticker] for ticker in valid_tickers], dtype=int)
                y = y_series.loc[valid_tickers].to_numpy(dtype=float)
                x = np.column_stack([np.ones(len(valid_tickers)), x_df.loc[valid_tickers].to_numpy(dtype=float)])
                q = orthonormal_basis(x, cfg.rank_tol)
                if len(valid_tickers) <= q.shape[1] + 1:
                    skipped_projections += 1
                    continue

                residual = residualize_vector_with_q(y, q)
                residual_array[date_pos, ticker_pos] = residual
                projections.append(TileProjection(batch_id, panel_id, int(date_pos), ticker_pos, x, q))
                ranks.append(q.shape[1])

    diagnostics = {
        "n_time_batches": int(len(time_batches)),
        "n_tiles": int(sum(len(panels) for panels in panels_by_batch)),
        "n_projections": int(len(projections)),
        "skipped_projections": int(skipped_projections),
        "min_panel_size": int(min(panel_sizes)) if panel_sizes else 0,
        "max_panel_size": int(max(panel_sizes)) if panel_sizes else 0,
        "median_effective_rank": float(np.median(ranks)) if ranks else np.nan,
        "n_regressors_with_intercept": int(n_regressors),
    }
    return MosaicWorkspace(dates, tickers, time_batches, panels_by_batch, projections, residual_array, diagnostics)


def block_bootstrap_within_mosaic_panels(
    observed_residuals: np.ndarray,
    workspace: MosaicWorkspace,
    rng: np.random.Generator,
    chunk_size: int,
) -> np.ndarray:
    n_dates, n_tickers = observed_residuals.shape
    out = np.full((chunk_size, n_dates, n_tickers), np.nan, dtype=float)
    batch_lengths = np.asarray([len(batch) for batch in workspace.time_batches])

    for rep in range(chunk_size):
        for batch_id, dest_block in enumerate(workspace.time_batches):
            eligible = np.flatnonzero(batch_lengths == len(dest_block))
            if len(eligible) == 0:
                eligible = np.arange(len(workspace.time_batches))
            for panel_pos in workspace.panels_by_batch[batch_id]:
                source_block = workspace.time_batches[int(rng.choice(eligible))]
                block_len = min(len(dest_block), len(source_block))
                out[rep][np.ix_(dest_block[:block_len], panel_pos)] = observed_residuals[np.ix_(source_block[:block_len], panel_pos)]
    return out


def re_residualize_bootstrap_chunk_to_basket(
    shuffled_residuals: np.ndarray,
    workspace: MosaicWorkspace,
    basket_pos: np.ndarray,
    cfg: Config,
) -> np.ndarray:
    n_reps = shuffled_residuals.shape[0]
    boot_basket = np.full((n_reps, len(workspace.dates), len(basket_pos)), np.nan, dtype=float)
    basket_pos_to_offset = {int(pos): i for i, pos in enumerate(basket_pos)}

    for proj in workspace.projections:
        local_indices: list[int] = []
        basket_offsets: list[int] = []
        for local_idx, global_pos in enumerate(proj.ticker_pos):
            offset = basket_pos_to_offset.get(int(global_pos))
            if offset is not None:
                local_indices.append(local_idx)
                basket_offsets.append(offset)
        if not local_indices:
            continue

        values = shuffled_residuals[:, proj.date_pos, proj.ticker_pos]
        if np.isfinite(values).all():
            residualized = residualize_matrix_with_q(values, proj.q)
        else:
            residualized = np.full_like(values, np.nan, dtype=float)
            for rep in range(n_reps):
                v = values[rep]
                finite = np.isfinite(v)
                if finite.all():
                    residualized[rep] = residualize_vector_with_q(v, proj.q)
                elif finite.sum() > 2:
                    x_sub = proj.x[finite]
                    q_sub = orthonormal_basis(x_sub, cfg.rank_tol)
                    if finite.sum() > q_sub.shape[1] + 1:
                        residualized[rep, finite] = residualize_vector_with_q(v[finite], q_sub)
        boot_basket[:, proj.date_pos, basket_offsets] = residualized[:, local_indices]
    return boot_basket


MOSAIC_WORKSPACE_CACHE: dict[tuple[pd.Timestamp, pd.Timestamp, int, int], MosaicWorkspace] = {}


def workspace_cache_key(dates: pd.Index, seed: int) -> tuple[pd.Timestamp, pd.Timestamp, int, int]:
    dates = pd.Index(pd.to_datetime(dates))
    return (pd.Timestamp(dates[0]), pd.Timestamp(dates[-1]), int(len(dates)), int(seed))


def get_mosaic_workspace(
    returns_wide: pd.DataFrame,
    exposure_by_date: dict[pd.Timestamp, pd.DataFrame],
    universe_by_date: dict[pd.Timestamp, set[str]],
    factor_names: list[str],
    dates: pd.Index,
    cfg: Config,
    seed: int,
) -> MosaicWorkspace:
    key = workspace_cache_key(dates, seed)
    if key not in MOSAIC_WORKSPACE_CACHE:
        MOSAIC_WORKSPACE_CACHE[key] = build_mosaic_workspace(
            returns_wide, exposure_by_date, universe_by_date, factor_names, dates, cfg, seed
        )
    return MOSAIC_WORKSPACE_CACHE[key]


def mosaic_bootstrap_apwc_tile_based(
    returns_wide: pd.DataFrame,
    exposure_by_date: dict[pd.Timestamp, pd.DataFrame],
    universe_by_date: dict[pd.Timestamp, set[str]],
    factor_names: list[str],
    dates: pd.Index,
    basket_tickers: list[str],
    reps: int,
    cfg: Config,
    workspace_seed: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    tic = time.perf_counter()
    workspace = get_mosaic_workspace(
        returns_wide, exposure_by_date, universe_by_date, factor_names, dates, cfg, workspace_seed
    )
    basket_tickers = [ticker for ticker in basket_tickers if ticker in workspace.tickers]
    if len(basket_tickers) < 2:
        return {
            "apwc": np.nan,
            "boot_mean": np.nan,
            "boot_std": np.nan,
            "z_score": np.nan,
            "n_boot": 0,
            "elapsed_sec": time.perf_counter() - tic,
            **workspace.diagnostics,
        }

    basket_pos = np.asarray([workspace.tickers.get_loc(ticker) for ticker in basket_tickers], dtype=int)
    observed_matrix = workspace.residual_array[:, basket_pos]
    observed_apwc = average_pairwise_corr_array(observed_matrix, cfg.min_obs_ratio)

    rng = np.random.default_rng(bootstrap_seed)
    boot_values: list[float] = []
    remaining = int(reps)
    while remaining > 0:
        chunk = min(cfg.bootstrap_chunk_size, remaining)
        remaining -= chunk
        shuffled = block_bootstrap_within_mosaic_panels(workspace.residual_array, workspace, rng, chunk)
        boot_basket = re_residualize_bootstrap_chunk_to_basket(shuffled, workspace, basket_pos, cfg)
        chunk_values = average_pairwise_corr_many(boot_basket, cfg.min_obs_ratio)
        boot_values.extend(float(v) for v in chunk_values if np.isfinite(v))

    boot = np.asarray(boot_values, dtype=float)
    boot_mean = float(np.mean(boot)) if len(boot) else np.nan
    boot_std = float(np.std(boot, ddof=1)) if len(boot) > 1 else np.nan
    z_score = float((observed_apwc - boot_mean) / boot_std) if np.isfinite(observed_apwc) and np.isfinite(boot_std) and boot_std > 0 else np.nan

    return {
        "apwc": float(observed_apwc) if np.isfinite(observed_apwc) else np.nan,
        "boot_mean": boot_mean,
        "boot_std": boot_std,
        "boot_q05": float(np.quantile(boot, 0.05)) if len(boot) else np.nan,
        "boot_q50": float(np.quantile(boot, 0.50)) if len(boot) else np.nan,
        "boot_q95": float(np.quantile(boot, 0.95)) if len(boot) else np.nan,
        "boot_se_mean": float(boot_std / np.sqrt(len(boot))) if len(boot) and np.isfinite(boot_std) else np.nan,
        "z_score": z_score,
        "n_boot": int(len(boot)),
        "elapsed_sec": float(time.perf_counter() - tic),
        **workspace.diagnostics,
    }


# ## 5. live/post-release 分析日での APWC z-score
# 
# 各テーマについて、公開日以降に過去60営業日と将来60営業日が両方取れる分析日を選びます。リリース日前後比較は行いません。

# In[8]:


def choose_analysis_dates(
    constituents: pd.DataFrame,
    trading_dates: pd.Index,
    cfg: Config,
) -> pd.DataFrame:
    rows = []
    trading_dates = pd.Index(pd.to_datetime(trading_dates)).sort_values()
    for theme_id, g in constituents.groupby("theme_id", sort=True):
        release_date = pd.to_datetime(g["release_date"].min())
        release_pos = int(np.searchsorted(trading_dates.values, np.datetime64(release_date), side="left"))
        first_pos = release_pos + cfg.window
        last_pos = len(trading_dates) - cfg.future_window - 1
        if first_pos > last_pos:
            continue
        candidates = trading_dates[first_pos : last_pos + 1]
        if len(candidates) == 0:
            continue
        if len(candidates) <= cfg.max_analysis_dates_per_theme:
            selected = candidates
        else:
            selected_idx = np.linspace(0, len(candidates) - 1, cfg.max_analysis_dates_per_theme).round().astype(int)
            selected = candidates[selected_idx]
        for analysis_date in selected:
            rows.append(
                {
                    "theme_id": theme_id,
                    "theme_name": g["theme_name"].iloc[0],
                    "release_date": release_date,
                    "analysis_date": pd.Timestamp(analysis_date),
                }
            )
    return pd.DataFrame(rows)


def bootstrap_reps_for_run(using_synthetic_data: bool, cfg: Config) -> int:
    override = os.getenv("THEMATIC_BOOTSTRAP_REPS")
    if override:
        return int(override)
    return cfg.bootstrap_reps_synthetic if using_synthetic_data else cfg.bootstrap_reps_real


def stable_theme_seed(theme_id: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate(str(theme_id)))


def analyze_theme_date(row: pd.Series, reps: int, cfg: Config) -> dict[str, Any]:
    theme_id = row["theme_id"]
    analysis_date = pd.Timestamp(row["analysis_date"])
    all_dates = pd.Index(pd.to_datetime(residuals_wide.index)).sort_values()
    pos = all_dates.get_loc(analysis_date)
    past_dates = all_dates[pos - cfg.window + 1 : pos + 1]
    future_dates = all_dates[pos + 1 : pos + 1 + cfg.future_window]
    assert len(past_dates) == cfg.window
    assert len(future_dates) == cfg.future_window
    assert max(past_dates) <= analysis_date
    assert min(future_dates) > analysis_date

    constituents_now = latest_constituents(theme_constituents, theme_id, analysis_date, public_only=True)
    basket_tickers = [ticker for ticker in constituents_now["ticker"] if ticker in returns_wide.columns]
    if len(basket_tickers) < cfg.min_members:
        raise ValueError(f"{theme_id} has fewer than {cfg.min_members} usable tickers at {analysis_date.date()}")

    workspace_seed = cfg.seed + int(pos) * 1009
    bootstrap_seed = workspace_seed + stable_theme_seed(theme_id) + 7919
    mosaic = mosaic_bootstrap_apwc_tile_based(
        returns_wide=returns_wide,
        exposure_by_date=exposure_by_date,
        universe_by_date=universe_by_date,
        factor_names=factor_names,
        dates=past_dates,
        basket_tickers=basket_tickers,
        reps=reps,
        cfg=cfg,
        workspace_seed=workspace_seed,
        bootstrap_seed=bootstrap_seed,
    )

    past_basket = basket_residual_return(residuals_wide.loc[past_dates], constituents_now)
    future_basket = basket_residual_return(residuals_wide.loc[future_dates], constituents_now)

    return {
        "theme_id": theme_id,
        "theme_name": row["theme_name"],
        "release_date": row["release_date"],
        "analysis_date": analysis_date,
        "past_start": pd.Timestamp(past_dates[0]),
        "past_end": pd.Timestamp(past_dates[-1]),
        "future_start": pd.Timestamp(future_dates[0]),
        "future_end": pd.Timestamp(future_dates[-1]),
        "n_members": len(basket_tickers),
        **mosaic,
        "is_coherent": bool(mosaic["z_score"] >= cfg.z_threshold) if np.isfinite(mosaic["z_score"]) else False,
        "past_residual_return": float(past_basket.sum()),
        "future_residual_return": float(future_basket.sum()),
        "feature_max_date": pd.Timestamp(past_dates[-1]),
        "label_min_date": pd.Timestamp(future_dates[0]),
        "mosaic_workspace_seed": int(workspace_seed),
        "bootstrap_seed": int(bootstrap_seed),
    }


analysis_calendar = choose_analysis_dates(theme_constituents, residuals_wide.index, cfg)
reps = bootstrap_reps_for_run(USING_SYNTHETIC_DATA, cfg)
print(f"analysis rows = {len(analysis_calendar)}, bootstrap reps per row = {reps}")
display(analysis_calendar)

analysis_start = time.perf_counter()
analysis_results = pd.DataFrame([analyze_theme_date(row, reps, cfg) for _, row in analysis_calendar.iterrows()])
analysis_elapsed_sec = time.perf_counter() - analysis_start

assert (analysis_results["feature_max_date"] <= analysis_results["analysis_date"]).all()
assert (analysis_results["label_min_date"] > analysis_results["analysis_date"]).all()
assert analysis_results["n_boot"].ge(max(10, int(reps * 0.80))).all(), "有効bootstrap標本数が少なすぎます。"

print(f"analysis elapsed seconds = {analysis_elapsed_sec:.3f}")
display(
    analysis_results[
        [
            "theme_id",
            "analysis_date",
            "n_members",
            "apwc",
            "boot_mean",
            "boot_std",
            "z_score",
            "is_coherent",
            "past_residual_return",
            "future_residual_return",
            "n_boot",
            "elapsed_sec",
            "n_time_batches",
            "n_tiles",
            "min_panel_size",
            "max_panel_size",
        ]
    ]
)


# ## 6. リスク過小評価の確認
# 
# 標準リスクモデルが残差共分散の非対角成分をゼロと置く場合と、過去窓の経験残差共分散を使う場合を比較します。

# In[9]:


def residual_risk_comparison(row: pd.Series, cfg: Config) -> dict[str, Any]:
    constituents_now = latest_constituents(theme_constituents, row["theme_id"], row["analysis_date"], public_only=True)
    tickers = [ticker for ticker in constituents_now["ticker"] if ticker in residuals_wide.columns]
    weights = constituents_now.set_index("ticker").loc[tickers, "weight"].astype(float)
    weights = weights / weights.sum()

    window = residuals_wide.loc[
        (residuals_wide.index >= row["past_start"]) & (residuals_wide.index <= row["past_end"]), tickers
    ]
    window = window.dropna(axis=1, thresh=int(np.ceil(len(window) * cfg.min_obs_ratio)))
    tickers = list(window.columns)
    if len(tickers) < 2:
        return {
            "theme_id": row["theme_id"],
            "analysis_date": row["analysis_date"],
            "is_coherent": row["is_coherent"],
            "apwc": row["apwc"],
            "model_residual_risk": np.nan,
            "empirical_residual_risk": np.nan,
            "risk_ratio_empirical_to_model": np.nan,
        }
    weights = weights.loc[tickers]
    weights = weights / weights.sum()

    cov = window.cov() * cfg.trading_days_per_year
    diag_cov = pd.DataFrame(np.diag(np.diag(cov.to_numpy())), index=cov.index, columns=cov.columns)
    w = weights.to_numpy()
    model_risk = float(np.sqrt(w @ diag_cov.to_numpy() @ w))
    empirical_risk = float(np.sqrt(max(w @ cov.to_numpy() @ w, 0.0)))
    return {
        "theme_id": row["theme_id"],
        "analysis_date": row["analysis_date"],
        "is_coherent": row["is_coherent"],
        "apwc": row["apwc"],
        "z_score": row["z_score"],
        "model_residual_risk": model_risk,
        "empirical_residual_risk": empirical_risk,
        "risk_ratio_empirical_to_model": empirical_risk / model_risk if model_risk > 0 else np.nan,
    }

risk_table = pd.DataFrame([residual_risk_comparison(row, cfg) for _, row in analysis_results.iterrows()])
display(risk_table)


# ## 7. Mosaic z-scoreに基づく残差リターン持続性
# 
# `z_score >= 2` のcoherent theme群と `z_score < 2` 群に分け、将来60営業日バスケット残差リターンを過去60営業日バスケット残差リターンで回帰します。

# In[10]:


def persistence_regression(results: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    rows = []
    for coherent_flag in [False, True]:
        g = results[results["is_coherent"].eq(coherent_flag)].copy()
        g = g.dropna(subset=["past_residual_return", "future_residual_return"])
        label = "z >= 2" if coherent_flag else "z < 2"
        base = {
            "group": label,
            "observations": int(len(g)),
            "n_themes": int(g["theme_id"].nunique()) if len(g) else 0,
        }
        if len(g) >= 3 and g["past_residual_return"].std(ddof=1) > 0:
            x = sm.add_constant(g["past_residual_return"], has_constant="add")
            y = g["future_residual_return"]
            ols = sm.OLS(y, x).fit()
            hc1 = sm.OLS(y, x).fit(cov_type="HC1")
            row = {
                **base,
                "estimated_coefficient": float(ols.params["past_residual_return"]),
                "t_stat_ols": float(ols.tvalues["past_residual_return"]),
                "t_stat_hc1": float(hc1.tvalues["past_residual_return"]),
                "r_squared": float(ols.rsquared),
                "status": "ok",
            }
            if g["theme_id"].nunique() >= 2 and len(g) > g["theme_id"].nunique():
                clustered = sm.OLS(y, x).fit(cov_type="cluster", cov_kwds={"groups": g["theme_id"]})
                row["t_stat_cluster_theme"] = float(clustered.tvalues["past_residual_return"])
            else:
                row["t_stat_cluster_theme"] = np.nan
            rows.append(row)
        else:
            rows.append(
                {
                    **base,
                    "estimated_coefficient": np.nan,
                    "t_stat_ols": np.nan,
                    "t_stat_hc1": np.nan,
                    "t_stat_cluster_theme": np.nan,
                    "r_squared": np.nan,
                    "status": "too_few_obs_or_zero_variance",
                }
            )
    return pd.DataFrame(rows)

persistence_table = persistence_regression(analysis_results, cfg)
display(persistence_table)


# ## 8. 実運用シグナル候補
# 
# APWC z-score `>= 2` をcoherenceゲートとし、過去残差リターンの符号をmomentum方向として使う最小シグナル表です。ここではコスト、流動性、サイズ制約、リスク予算、Barraファクター回帰は扱いません。

# In[11]:


def build_operational_signal_table(results: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    signal = results.copy()
    signal["coherence_gate"] = signal["z_score"] >= cfg.z_threshold
    signal["residual_momentum_direction"] = np.sign(signal["past_residual_return"]).astype(float)
    signal["long_theme_candidate"] = signal["coherence_gate"] & (signal["past_residual_return"] > 0)
    signal["underweight_or_short_candidate"] = signal["coherence_gate"] & (signal["past_residual_return"] < 0)
    signal["signed_future_residual_return"] = signal["residual_momentum_direction"] * signal["future_residual_return"]
    signal["raw_signal_score"] = np.where(signal["coherence_gate"], signal["z_score"] * signal["past_residual_return"], 0.0)
    signal["position_hint"] = np.select(
        [signal["long_theme_candidate"], signal["underweight_or_short_candidate"]],
        ["long coherent residual momentum", "underweight/short coherent negative residual momentum"],
        default="no coherent residual momentum signal",
    )
    return signal.sort_values(["analysis_date", "raw_signal_score"], ascending=[True, False]).reset_index(drop=True)


def summarize_operational_signal(signal: pd.DataFrame) -> pd.DataFrame:
    rows = []
    variants = {
        "coherent_signed_residual_momentum": signal[signal["coherence_gate"]].copy(),
        "coherent_long_positive_residual_momentum": signal[signal["long_theme_candidate"]].copy(),
        "all_signed_residual_momentum_baseline": signal.copy(),
    }
    for name, g in variants.items():
        if g.empty:
            rows.append({"strategy_diagnostic": name, "observations": 0})
            continue
        if name.endswith("signed_residual_momentum") or name == "all_signed_residual_momentum_baseline":
            eval_return = g["signed_future_residual_return"]
        else:
            eval_return = g["future_residual_return"]
        rows.append(
            {
                "strategy_diagnostic": name,
                "observations": int(len(g)),
                "n_themes": int(g["theme_id"].nunique()),
                "mean_eval_residual_return": float(eval_return.mean()),
                "t_stat_simple": float(eval_return.mean() / (eval_return.std(ddof=1) / np.sqrt(len(eval_return)))) if len(eval_return) > 1 and eval_return.std(ddof=1) > 0 else np.nan,
                "win_rate": float((eval_return > 0).mean()),
            }
        )
    return pd.DataFrame(rows)

operational_signal_table = build_operational_signal_table(analysis_results, cfg)
operational_signal_summary = summarize_operational_signal(operational_signal_table)

display(
    operational_signal_table[
        [
            "theme_id",
            "analysis_date",
            "z_score",
            "coherence_gate",
            "past_residual_return",
            "future_residual_return",
            "signed_future_residual_return",
            "raw_signal_score",
            "position_hint",
        ]
    ]
)
display(operational_signal_summary)


# ## 9. 検証サマリー

# In[12]:


validation_report = {
    "using_synthetic_data": USING_SYNTHETIC_DATA,
    "real_data_validation": "not_run_synthetic_mode" if USING_SYNTHETIC_DATA else "schema_loaded_and_executed",
    "release_prepost_analysis_included": False,
    "tile_based_mosaic_bootstrap": True,
    "mosaic_batch_size": cfg.mosaic_batch_size,
    "mosaic_panel_min_factor_multiplier": cfg.mosaic_panel_min_factor_multiplier,
    "bootstrap_reps_per_row": int(reps),
    "bootstrap_chunk_size": cfg.bootstrap_chunk_size,
    "workspace_cache_entries": int(len(MOSAIC_WORKSPACE_CACHE)),
    "n_themes": int(theme_constituents["theme_id"].nunique()),
    "n_tickers": int(stock_total_returns["ticker"].nunique()),
    "n_return_dates": int(stock_total_returns["date"].nunique()),
    "n_analysis_rows": int(len(analysis_results)),
    "n_coherent_rows": int(analysis_results["is_coherent"].sum()),
    "max_abs_daily_residual_mean": float(max_abs_residual_mean),
    "feature_label_timing_ok": bool((analysis_results["feature_max_date"] <= analysis_results["analysis_date"]).all() and (analysis_results["label_min_date"] > analysis_results["analysis_date"]).all()),
    "analysis_elapsed_sec": float(analysis_elapsed_sec),
    "median_row_bootstrap_elapsed_sec": float(analysis_results["elapsed_sec"].median()),
    "return_persistence_available": bool(not persistence_table.empty),
    "operational_signal_table_available": bool(not operational_signal_table.empty),
}

display(pd.Series(validation_report, name="validation_report"))

summary_by_theme = analysis_results.groupby("theme_id").agg(
    theme_name=("theme_name", "first"),
    rows=("theme_id", "size"),
    mean_apwc=("apwc", "mean"),
    mean_z=("z_score", "mean"),
    coherent_rate=("is_coherent", "mean"),
    mean_past_residual_return=("past_residual_return", "mean"),
    mean_future_residual_return=("future_residual_return", "mean"),
).join(
    risk_table.groupby("theme_id")["risk_ratio_empirical_to_model"].mean().rename("mean_risk_ratio")
)
display(summary_by_theme)

print("persistence_table")
display(persistence_table)
print("operational_signal_summary")
display(operational_signal_summary)

