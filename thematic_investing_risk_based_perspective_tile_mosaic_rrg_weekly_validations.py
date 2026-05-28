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


# ## 9. RRG-like residual RS-Ratio / RS-Momentum suite
#
# APWC Mosaic + bootstrap z-score は coherent theme gate として残し、RRG-like 指標は方向・タイミング・ランキングのために計算します。
# ここでは以下をすべて出力します。
#
# - Residual Return RRG: 残差RS-Ratio / 残差RS-Momentum / 象限
# - Pattern A: APWC gate + quadrant rule
# - Pattern B: APWC gate + continuous RRG score
# - Pattern C: quadrant transition rule
# - Coherence RRG: APWC z-score水準と変化量によるライフサイクル判定
# - Two-layer overlay: Coherence RRG と Residual Return RRG の合成シグナル

# In[12]:


@dataclass(frozen=True)
class RRGConfig:
    z_threshold: float = cfg.z_threshold
    z_cap: float = 5.0
    rs_ratio_center: float = 100.0
    rs_ratio_scale: float = 10.0
    rs_momentum_lag_periods: int = 1
    standardization_lookback: int = 12
    standardization_min_periods: int = 2
    alpha_ratio: float = 0.50
    beta_momentum: float = 0.50
    use_transition_for_pattern_a: bool = True


rrg_cfg = RRGConfig()


def _safe_sign(x: Any) -> float:
    try:
        if not np.isfinite(x) or abs(float(x)) < 1e-12:
            return 0.0
        return float(np.sign(x))
    except Exception:
        return 0.0


def coherence_weight_from_z(z: float, rrg_cfg: RRGConfig) -> float:
    if not np.isfinite(z):
        return 0.0
    denom = max(rrg_cfg.z_cap - rrg_cfg.z_threshold, 1e-12)
    return float(np.clip((z - rrg_cfg.z_threshold) / denom, 0.0, 1.0))


def zscore_against_prior_history(
    series: pd.Series,
    lookback: int,
    min_periods: int,
) -> pd.Series:
    history = series.astype(float).shift(1)
    mean = history.rolling(lookback, min_periods=min_periods).mean()
    std = history.rolling(lookback, min_periods=min_periods).std(ddof=1)
    return (series.astype(float) - mean) / std.replace(0.0, np.nan)


def cross_sectional_zscore(panel: pd.DataFrame, value_col: str, date_col: str = "analysis_date") -> pd.Series:
    def _z(g: pd.DataFrame) -> pd.Series:
        x = g[value_col].astype(float)
        s = x.std(ddof=1)
        if len(x) < 2 or not np.isfinite(s) or s <= 0:
            return pd.Series(np.nan, index=g.index)
        return (x - x.mean()) / s
    return panel.groupby(date_col, group_keys=False).apply(_z)


def add_residual_rrg_benchmark(
    panel: pd.DataFrame,
    risk_table: pd.DataFrame | None = None,
    benchmark_mode: str = "zero",
    date_col: str = "analysis_date",
) -> pd.DataFrame:
    out = panel.copy()
    if benchmark_mode == "zero":
        out["rrg_benchmark_residual_return"] = 0.0
    elif benchmark_mode == "cross_section_equal":
        out["rrg_benchmark_residual_return"] = out.groupby(date_col)["past_residual_return"].transform("mean")
    elif benchmark_mode == "cross_section_risk_weighted":
        if risk_table is None or risk_table.empty:
            out["rrg_benchmark_residual_return"] = out.groupby(date_col)["past_residual_return"].transform("mean")
        else:
            risk_cols = ["theme_id", "analysis_date", "empirical_residual_risk", "model_residual_risk"]
            available_cols = [c for c in risk_cols if c in risk_table.columns]
            merged = out.merge(risk_table[available_cols], on=["theme_id", "analysis_date"], how="left")
            risk = merged.get("empirical_residual_risk", pd.Series(np.nan, index=merged.index)).astype(float)
            if risk.isna().all() and "model_residual_risk" in merged:
                risk = merged["model_residual_risk"].astype(float)
            inv_risk = 1.0 / risk.replace(0.0, np.nan)
            merged["_rrg_inv_risk_weight"] = inv_risk.replace([np.inf, -np.inf], np.nan)

            def _weighted_benchmark(g: pd.DataFrame) -> pd.Series:
                w = g["_rrg_inv_risk_weight"].astype(float)
                r = g["past_residual_return"].astype(float)
                valid = w.notna() & r.notna()
                if valid.sum() < 2 or w.loc[valid].sum() <= 0:
                    bench = r.mean()
                else:
                    bench = float(np.average(r.loc[valid], weights=w.loc[valid]))
                return pd.Series(bench, index=g.index)

            out["rrg_benchmark_residual_return"] = merged.groupby(date_col, group_keys=False).apply(_weighted_benchmark).reindex(merged.index).to_numpy()
    else:
        raise ValueError(f"Unknown benchmark_mode: {benchmark_mode}")
    out["rrg_benchmark_mode"] = benchmark_mode
    out["rrg_relative_residual_return"] = out["past_residual_return"].astype(float) - out["rrg_benchmark_residual_return"].astype(float)
    return out


def add_residual_rrg_axes(
    panel: pd.DataFrame,
    rrg_cfg: RRGConfig,
    standardization: str = "time_series",
    date_col: str = "analysis_date",
) -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["rrg_rs_momentum_raw"] = out.groupby("theme_id")["rrg_relative_residual_return"].diff(rrg_cfg.rs_momentum_lag_periods)

    if standardization == "time_series":
        out["rrg_rs_ratio_z"] = out.groupby("theme_id", group_keys=False)["rrg_relative_residual_return"].apply(
            lambda s: zscore_against_prior_history(s, rrg_cfg.standardization_lookback, rrg_cfg.standardization_min_periods)
        )
        out["rrg_rs_momentum_z"] = out.groupby("theme_id", group_keys=False)["rrg_rs_momentum_raw"].apply(
            lambda s: zscore_against_prior_history(s, rrg_cfg.standardization_lookback, rrg_cfg.standardization_min_periods)
        )
    elif standardization == "cross_sectional":
        out["rrg_rs_ratio_z"] = cross_sectional_zscore(out, "rrg_relative_residual_return", date_col=date_col)
        out["rrg_rs_momentum_z"] = cross_sectional_zscore(out, "rrg_rs_momentum_raw", date_col=date_col)
    elif standardization == "expanding_time_series":
        out["rrg_rs_ratio_z"] = out.groupby("theme_id", group_keys=False)["rrg_relative_residual_return"].apply(
            lambda s: (s - s.shift(1).expanding(rrg_cfg.standardization_min_periods).mean())
            / s.shift(1).expanding(rrg_cfg.standardization_min_periods).std(ddof=1).replace(0.0, np.nan)
        )
        out["rrg_rs_momentum_z"] = out.groupby("theme_id", group_keys=False)["rrg_rs_momentum_raw"].apply(
            lambda s: (s - s.shift(1).expanding(rrg_cfg.standardization_min_periods).mean())
            / s.shift(1).expanding(rrg_cfg.standardization_min_periods).std(ddof=1).replace(0.0, np.nan)
        )
    else:
        raise ValueError(f"Unknown standardization: {standardization}")

    out["rrg_standardization"] = standardization
    out["rs_ratio"] = rrg_cfg.rs_ratio_center + rrg_cfg.rs_ratio_scale * out["rrg_rs_ratio_z"]
    out["rs_momentum"] = rrg_cfg.rs_ratio_center + rrg_cfg.rs_ratio_scale * out["rrg_rs_momentum_z"]
    return out


def classify_rrg_quadrant(rs_ratio: float, rs_momentum: float, center: float = 100.0) -> str:
    if not np.isfinite(rs_ratio) or not np.isfinite(rs_momentum):
        return "Undefined"
    if rs_ratio >= center and rs_momentum >= center:
        return "Leading"
    if rs_ratio >= center and rs_momentum < center:
        return "Weakening"
    if rs_ratio < center and rs_momentum < center:
        return "Lagging"
    return "Improving"


def direction_from_rrg_quadrant(quadrant: str) -> int:
    if quadrant == "Leading":
        return 1
    if quadrant == "Lagging":
        return -1
    return 0


def add_rrg_quadrants_and_transitions(panel: pd.DataFrame, rrg_cfg: RRGConfig, date_col: str = "analysis_date") -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["rrg_quadrant"] = [
        classify_rrg_quadrant(x, y, center=rrg_cfg.rs_ratio_center)
        for x, y in zip(out["rs_ratio"], out["rs_momentum"])
    ]
    out["prior_rrg_quadrant"] = out.groupby("theme_id")["rrg_quadrant"].shift(1)
    out["rrg_transition"] = out["prior_rrg_quadrant"].fillna("Start") + " -> " + out["rrg_quadrant"].astype(str)
    out["rrg_quadrant_direction"] = out["rrg_quadrant"].map(direction_from_rrg_quadrant).astype(int)

    def _transition_direction(row: pd.Series) -> int:
        prev_q, q = row["prior_rrg_quadrant"], row["rrg_quadrant"]
        if q == "Leading" or (prev_q == "Improving" and q == "Leading"):
            return 1
        if q == "Lagging" or (prev_q == "Weakening" and q == "Lagging"):
            return -1
        return 0

    out["rrg_transition_direction"] = out.apply(_transition_direction, axis=1).astype(int)
    return out


def add_coherence_rrg(panel: pd.DataFrame, rrg_cfg: RRGConfig, date_col: str = "analysis_date") -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["coherence_z"] = out["z_score"].astype(float)
    out["coherence_delta_z"] = out.groupby("theme_id")["coherence_z"].diff()

    def _state(row: pd.Series) -> str:
        z = row["coherence_z"]
        dz = row["coherence_delta_z"]
        if not np.isfinite(z):
            return "Undefined"
        if not np.isfinite(dz):
            return "Active coherent" if z >= rrg_cfg.z_threshold else "Unconfirmed"
        if z >= rrg_cfg.z_threshold and dz >= 0:
            return "Active coherent"
        if z >= rrg_cfg.z_threshold and dz < 0:
            return "Mature coherent"
        if z < rrg_cfg.z_threshold and dz >= 0:
            return "Emerging coherent"
        return "Dormant/dead"

    out["coherence_rrg_state"] = out.apply(_state, axis=1)
    out["coherence_lifecycle_weight"] = out["coherence_rrg_state"].map(
        {
            "Active coherent": 1.00,
            "Mature coherent": 0.50,
            "Emerging coherent": 0.25,
            "Dormant/dead": 0.00,
            "Unconfirmed": 0.00,
            "Undefined": 0.00,
        }
    ).astype(float)
    return out


def add_rrg_signal_patterns(panel: pd.DataFrame, rrg_cfg: RRGConfig) -> pd.DataFrame:
    out = panel.copy()
    out["coherence_gate"] = out["z_score"].astype(float) >= rrg_cfg.z_threshold
    out["coherence_weight"] = out["z_score"].astype(float).map(lambda z: coherence_weight_from_z(z, rrg_cfg))

    def _pattern_a(row: pd.Series) -> str:
        if not bool(row["coherence_gate"]):
            return "no_position_not_coherent"
        q = row["rrg_quadrant"]
        prev_q = row["prior_rrg_quadrant"]
        if q == "Leading" or (rrg_cfg.use_transition_for_pattern_a and prev_q == "Improving" and q == "Leading"):
            return "long"
        if q == "Lagging" or (rrg_cfg.use_transition_for_pattern_a and prev_q == "Weakening" and q == "Lagging"):
            return "underweight_or_short"
        if q == "Weakening":
            return "hold_or_reduce"
        if q == "Improving":
            return "watchlist"
        return "no_position_rrg_undefined"

    out["pattern_a_quadrant_signal"] = out.apply(_pattern_a, axis=1)
    out["pattern_a_position"] = out["pattern_a_quadrant_signal"].map(
        {"long": 1, "underweight_or_short": -1, "hold_or_reduce": 0, "watchlist": 0}
    ).fillna(0).astype(int)

    raw_score = rrg_cfg.alpha_ratio * out["rrg_rs_ratio_z"].astype(float) + rrg_cfg.beta_momentum * out["rrg_rs_momentum_z"].astype(float)
    out["pattern_b_rrg_raw_score"] = raw_score
    out["pattern_b_score"] = out["coherence_weight"] * raw_score.fillna(0.0)
    out["pattern_b_position"] = out["pattern_b_score"].map(_safe_sign)

    out["pattern_c_transition_score"] = out["coherence_weight"] * out["rrg_transition_direction"].astype(float)
    out["pattern_c_position"] = out["pattern_c_transition_score"].map(_safe_sign)

    out["two_layer_score"] = out["coherence_weight"] * out["coherence_lifecycle_weight"] * raw_score.fillna(0.0)
    out["two_layer_position"] = out["two_layer_score"].map(_safe_sign)
    out["two_layer_watchlist"] = out["coherence_rrg_state"].eq("Emerging coherent") & out["rrg_quadrant"].isin(["Improving", "Leading"])
    return out


def build_rrg_suite(
    signal_panel: pd.DataFrame,
    risk_table: pd.DataFrame | None,
    rrg_cfg: RRGConfig,
    benchmark_modes: list[str] | None = None,
    standardizations: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    if benchmark_modes is None:
        benchmark_modes = ["zero", "cross_section_equal", "cross_section_risk_weighted"]
    if standardizations is None:
        standardizations = ["time_series", "cross_sectional", "expanding_time_series"]
    panels: dict[str, pd.DataFrame] = {}
    base_cols = [
        "theme_id",
        "theme_name",
        "release_date",
        "analysis_date",
        "z_score",
        "apwc",
        "past_residual_return",
        "future_residual_return",
        "n_members",
    ]
    base = signal_panel[[c for c in base_cols if c in signal_panel.columns]].copy()
    for benchmark_mode in benchmark_modes:
        b = add_residual_rrg_benchmark(base, risk_table=risk_table, benchmark_mode=benchmark_mode)
        for standardization in standardizations:
            p = add_residual_rrg_axes(b, rrg_cfg=rrg_cfg, standardization=standardization)
            p = add_rrg_quadrants_and_transitions(p, rrg_cfg=rrg_cfg)
            p = add_coherence_rrg(p, rrg_cfg=rrg_cfg)
            p = add_rrg_signal_patterns(p, rrg_cfg=rrg_cfg)
            key = f"{benchmark_mode}__{standardization}"
            panels[key] = p.sort_values(["analysis_date", "theme_id"]).reset_index(drop=True)
    return panels


def summarize_rrg_panel(panel: pd.DataFrame, panel_name: str) -> pd.DataFrame:
    rows = []
    for signal_col, position_col in [
        ("pattern_a_quadrant_signal", "pattern_a_position"),
        ("pattern_b_score", "pattern_b_position"),
        ("pattern_c_transition_score", "pattern_c_position"),
        ("two_layer_score", "two_layer_position"),
    ]:
        p = panel.copy()
        p["position"] = p[position_col].astype(float)
        p["signed_future_residual_return"] = p["position"] * p["future_residual_return"].astype(float)
        invested = p[p["position"].abs() > 0]
        rows.append(
            {
                "rrg_panel": panel_name,
                "method": signal_col,
                "rows": int(len(p)),
                "invested_rows": int(len(invested)),
                "long_rows": int((p["position"] > 0).sum()),
                "short_rows": int((p["position"] < 0).sum()),
                "invested_rate": float((p["position"].abs() > 0).mean()) if len(p) else np.nan,
                "mean_signed_future_resid_when_invested": float(invested["signed_future_residual_return"].mean()) if len(invested) else np.nan,
                "t_signed_future_resid_when_invested": simple_t_stat(invested["signed_future_residual_return"]) if len(invested) else np.nan,
                "win_rate_when_invested": float((invested["signed_future_residual_return"] > 0).mean()) if len(invested) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def simple_t_stat(series: pd.Series | np.ndarray) -> float:
    x = pd.Series(series).dropna().astype(float)
    if len(x) < 2:
        return np.nan
    sd = x.std(ddof=1)
    if not np.isfinite(sd) or sd <= 0:
        return np.nan
    return float(x.mean() / (sd / np.sqrt(len(x))))


rrg_panels = build_rrg_suite(operational_signal_table, risk_table, rrg_cfg)
rrg_default_key = "zero__time_series"
rrg_signal_panel = rrg_panels[rrg_default_key]
rrg_summary = pd.concat([summarize_rrg_panel(panel, key) for key, panel in rrg_panels.items()], ignore_index=True)

print("RRG config")
display(pd.Series(rrg_cfg.__dict__))
print(f"Default RRG panel: {rrg_default_key}")
display(
    rrg_signal_panel[
        [
            "theme_id",
            "analysis_date",
            "z_score",
            "coherence_gate",
            "coherence_rrg_state",
            "rrg_relative_residual_return",
            "rs_ratio",
            "rs_momentum",
            "rrg_quadrant",
            "rrg_transition",
            "pattern_a_quadrant_signal",
            "pattern_b_score",
            "pattern_c_transition_score",
            "two_layer_score",
            "future_residual_return",
        ]
    ]
)
print("RRG method summary across benchmark / standardization variants")
display(rrg_summary)


# ## 10. Weekly APWC rolling-Z gated momentum strategy: 参考実装と妥当性検証設計
#
# この節は論文の主分析からは意図的に外れます。APWCのMosaic z-scoreではなく、テーマ自身の過去APWC履歴に対するrolling-Zを使うため、coherent themeの統計検定ではありません。
# ただし、実運用頻度・エントリー/エグジット設計の参考として、total momentum / residual momentum、APWC rolling-Z gate、閾値スイープ、IC、簡易回帰、戦略診断を計算します。

# In[13]:


@dataclass(frozen=True)
class WeeklyMomentumConfig:
    signal_window: int = cfg.window
    apwc_z_lookback_weeks: int = 12
    apwc_z_min_periods: int = 4
    apwc_z_threshold: float = 0.0
    top_momentum_n: int = 1
    min_members: int = 2
    annualization_weeks: int = 52
    threshold_grid: tuple[float, ...] = (0.0, 1.0, 2.0)
    top_n_grid: tuple[int, ...] = (1, 2)
    rrg_return_modes: tuple[str, ...] = ("residual", "total")
    rrg_benchmark_modes: tuple[str, ...] = ("zero", "cross_section_equal")
    rrg_standardizations: tuple[str, ...] = ("time_series", "cross_sectional", "expanding_time_series")
    rolling_z_soft_threshold_high: float = 1.5
    rrg_score_threshold: float = 0.0
    rrg_placebo_reps: int = int(os.getenv("THEMATIC_WEEKLY_RRG_PLACEBO_REPS", "30"))
    transaction_cost_bps_grid: tuple[float, ...] = (0.0, 5.0, 10.0, 25.0)
    walkforward_train_fraction: float = 0.50


weekly_cfg = WeeklyMomentumConfig()


def basket_weighted_return(return_window: pd.DataFrame, constituent_df: pd.DataFrame) -> pd.Series:
    tickers = [ticker for ticker in constituent_df["ticker"] if ticker in return_window.columns]
    if len(tickers) == 0:
        return pd.Series(index=return_window.index, dtype=float)
    weights = constituent_df.set_index("ticker").loc[tickers, "weight"].astype(float)
    weights = weights / weights.sum()
    return return_window[tickers].mul(weights, axis=1).sum(axis=1, min_count=1)


def weekly_rebalance_dates(trading_index: pd.Index) -> pd.Index:
    idx = pd.Index(pd.to_datetime(trading_index)).sort_values()
    weekly = idx.to_series(index=idx).groupby(idx.to_period("W-FRI")).max()
    return pd.Index(weekly.dropna()).sort_values()


def add_apwc_rolling_z(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    if panel.empty:
        return panel.copy()
    panel = panel.sort_values(["theme_id", "analysis_date"]).copy()
    pieces = []
    for _, g in panel.groupby("theme_id", sort=True):
        g = g.copy()
        apwc = g["apwc"].astype(float)
        history = apwc.shift(1)
        mean = history.rolling(strategy_cfg.apwc_z_lookback_weeks, min_periods=strategy_cfg.apwc_z_min_periods).mean()
        std = history.rolling(strategy_cfg.apwc_z_lookback_weeks, min_periods=strategy_cfg.apwc_z_min_periods).std(ddof=1)
        g["apwc_rolling_mean_prior"] = mean
        g["apwc_rolling_std_prior"] = std
        g["apwc_rolling_z"] = (apwc - mean) / std.replace(0.0, np.nan)
        pieces.append(g)
    out = pd.concat(pieces, ignore_index=True)
    out["apwc_gate"] = out["apwc_rolling_z"] >= strategy_cfg.apwc_z_threshold
    return out.sort_values(["analysis_date", "theme_id"]).reset_index(drop=True)


def build_weekly_coherence_momentum_panel(strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    all_dates = pd.Index(pd.to_datetime(returns_wide.index)).sort_values()
    rebal_dates = weekly_rebalance_dates(all_dates)
    rows = []
    for i, analysis_date in enumerate(rebal_dates[:-1]):
        analysis_date = pd.Timestamp(analysis_date)
        pos = all_dates.get_loc(analysis_date)
        if pos < strategy_cfg.signal_window - 1:
            continue
        next_rebalance = pd.Timestamp(rebal_dates[i + 1])
        past_dates = all_dates[pos - strategy_cfg.signal_window + 1 : pos + 1]
        future_dates = all_dates[(all_dates > analysis_date) & (all_dates <= next_rebalance)]
        if len(future_dates) == 0:
            continue
        for theme_id, g in theme_constituents.groupby("theme_id", sort=True):
            constituents_now = latest_constituents(theme_constituents, theme_id, analysis_date, public_only=True)
            if constituents_now.empty:
                continue
            tickers = [ticker for ticker in constituents_now["ticker"] if ticker in residuals_wide.columns]
            if len(tickers) < strategy_cfg.min_members:
                continue
            past_total = basket_weighted_return(returns_wide.loc[past_dates], constituents_now)
            future_total = basket_weighted_return(returns_wide.loc[future_dates], constituents_now)
            past_resid = basket_residual_return(residuals_wide.loc[past_dates], constituents_now)
            future_resid = basket_residual_return(residuals_wide.loc[future_dates], constituents_now)
            rows.append(
                {
                    "mode": "weekly_apwc_rolling_z_reference",
                    "theme_id": theme_id,
                    "theme_name": g["theme_name"].iloc[0],
                    "analysis_date": analysis_date,
                    "rebalance_date": analysis_date,
                    "next_rebalance_date": next_rebalance,
                    "past_start": pd.Timestamp(past_dates[0]),
                    "past_end": pd.Timestamp(past_dates[-1]),
                    "future_start": pd.Timestamp(future_dates[0]),
                    "future_end": pd.Timestamp(future_dates[-1]),
                    "n_members": len(tickers),
                    "apwc": average_pairwise_corr(residuals_wide.loc[past_dates, tickers]),
                    "past_total_momentum": float(past_total.sum()),
                    "past_residual_momentum": float(past_resid.sum()),
                    "future_total_return": float(future_total.sum()),
                    "future_residual_return": float(future_resid.sum()),
                }
            )
    panel = pd.DataFrame(rows)
    if panel.empty:
        return panel
    panel = add_apwc_rolling_z(panel, strategy_cfg)
    assert (panel["past_end"] <= panel["analysis_date"]).all()
    assert (panel["future_start"] > panel["analysis_date"]).all()
    return panel


def _select_top_by_momentum(g: pd.DataFrame, momentum_col: str, top_n: int) -> pd.DataFrame:
    clean = g.dropna(subset=[momentum_col, "future_total_return", "future_residual_return"])
    if clean.empty:
        return clean
    return clean.sort_values(momentum_col, ascending=False).head(top_n)


def weekly_factor_sums(start: pd.Timestamp, end: pd.Timestamp) -> dict[str, float]:
    window = factor_returns.loc[(factor_returns.index >= start) & (factor_returns.index <= end)]
    if window.empty:
        return {f"factor_{col}": 0.0 for col in factor_returns.columns}
    return {f"factor_{col}": float(window[col].sum()) for col in factor_returns.columns}


def build_weekly_strategy_returns(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
    apwc_z_threshold: float | None = None,
    top_n: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    strategy_rows = []
    selection_rows = []
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    if apwc_z_threshold is None:
        apwc_z_threshold = strategy_cfg.apwc_z_threshold
    if top_n is None:
        top_n = strategy_cfg.top_momentum_n

    strategy_specs = [
        ("weekly_total_momentum_all", "past_total_momentum", False),
        ("weekly_total_momentum_apwc_rolling_z_gate", "past_total_momentum", True),
        ("weekly_residual_momentum_all", "past_residual_momentum", False),
        ("weekly_residual_momentum_apwc_rolling_z_gate", "past_residual_momentum", True),
    ]
    for analysis_date, g in panel.groupby("analysis_date", sort=True):
        candidates = g.dropna(subset=["future_total_return", "future_residual_return"])
        for strategy, momentum_col, use_gate in strategy_specs:
            base = candidates[candidates["apwc_rolling_z"] >= apwc_z_threshold] if use_gate else candidates
            selected = _select_top_by_momentum(base, momentum_col, top_n)
            invested = not selected.empty
            future_start = candidates["future_start"].min() if not candidates.empty else pd.NaT
            future_end = candidates["future_end"].max() if not candidates.empty else pd.NaT
            row = {
                "strategy": strategy,
                "analysis_date": pd.Timestamp(analysis_date),
                "future_start": future_start,
                "future_end": future_end,
                "apwc_z_threshold": float(apwc_z_threshold),
                "top_n": int(top_n),
                "momentum_col": momentum_col,
                "strategy_return": float(selected["future_total_return"].mean()) if invested else 0.0,
                "strategy_residual_return": float(selected["future_residual_return"].mean()) if invested else 0.0,
                "n_selected": int(len(selected)),
                "invested": bool(invested),
            }
            if invested:
                row.update(weekly_factor_sums(selected["future_start"].min(), selected["future_end"].max()))
                tmp = selected.copy()
                tmp["strategy"] = strategy
                tmp["portfolio_weight"] = 1.0 / len(tmp)
                tmp["apwc_z_threshold"] = float(apwc_z_threshold)
                tmp["top_n"] = int(top_n)
                selection_rows.append(tmp)
            else:
                row.update({f"factor_{col}": 0.0 for col in factor_returns.columns})
            strategy_rows.append(row)
    return pd.DataFrame(strategy_rows), pd.concat(selection_rows, ignore_index=True) if selection_rows else pd.DataFrame()


def summarize_weekly_strategy(strategy_panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    rows = []
    if strategy_panel.empty:
        return pd.DataFrame()
    for keys, g in strategy_panel.groupby(["strategy", "apwc_z_threshold", "top_n"], sort=True):
        strategy, threshold, top_n = keys
        returns = g["strategy_return"].astype(float)
        residual_returns = g["strategy_residual_return"].astype(float)
        vol = returns.std(ddof=1)
        rows.append(
            {
                "strategy": strategy,
                "apwc_z_threshold": float(threshold),
                "top_n": int(top_n),
                "n_weeks": int(len(g)),
                "n_invested_weeks": int(g["invested"].sum()),
                "invested_rate": float(g["invested"].mean()) if len(g) else np.nan,
                "mean_weekly_return": float(returns.mean()) if len(g) else np.nan,
                "weekly_return_t": simple_t_stat(returns),
                "weekly_win_rate": float((returns > 0).mean()) if len(g) else np.nan,
                "mean_weekly_residual_return": float(residual_returns.mean()) if len(g) else np.nan,
                "weekly_residual_t": simple_t_stat(residual_returns),
                "annualized_return_approx": float(returns.mean() * strategy_cfg.annualization_weeks) if len(g) else np.nan,
                "annualized_vol_approx": float(vol * np.sqrt(strategy_cfg.annualization_weeks)) if len(g) > 1 else np.nan,
                "sharpe_approx": float((returns.mean() / vol) * np.sqrt(strategy_cfg.annualization_weeks)) if len(g) > 1 and np.isfinite(vol) and vol > 0 else np.nan,
                "compound_return": float((1.0 + returns).prod() - 1.0) if len(g) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def run_factor_decomposition(strategy_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if strategy_panel.empty:
        return pd.DataFrame()
    factor_cols = [c for c in strategy_panel.columns if c.startswith("factor_")]
    for strategy, g in strategy_panel.groupby("strategy", sort=True):
        if len(g) < max(4, len(factor_cols) + 2):
            rows.append({"strategy": strategy, "status": "too_few_obs", "n_obs": int(len(g))})
            continue
        y = g["strategy_return"].astype(float)
        x = g[factor_cols].astype(float).copy()
        x = sm.add_constant(x, has_constant="add")
        try:
            model = sm.OLS(y, x, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": min(4, max(1, len(g) // 4))})
            rows.append(
                {
                    "strategy": strategy,
                    "status": "ok",
                    "n_obs": int(model.nobs),
                    "alpha_weekly": float(model.params.get("const", np.nan)),
                    "alpha_t": float(model.tvalues.get("const", np.nan)),
                    "r_squared": float(model.rsquared),
                }
            )
        except Exception as exc:
            rows.append({"strategy": strategy, "status": f"failed: {exc}", "n_obs": int(len(g))})
    return pd.DataFrame(rows)



def fast_spearman_corr(x: pd.Series, y: pd.Series) -> float:
    """Small-sample Spearman correlation without constructing temporary DataFrames."""
    xv = np.asarray(x, dtype=float)
    yv = np.asarray(y, dtype=float)
    valid = np.isfinite(xv) & np.isfinite(yv)
    xv = xv[valid]
    yv = yv[valid]
    if xv.size < 3 or np.unique(xv).size < 2 or np.unique(yv).size < 2:
        return np.nan
    xr = pd.Series(xv).rank(method="average").to_numpy(dtype=float)
    yr = pd.Series(yv).rank(method="average").to_numpy(dtype=float)
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    denom = float(np.sqrt(np.dot(xr, xr) * np.dot(yr, yr)))
    if denom <= 0 or not np.isfinite(denom):
        return np.nan
    return float(np.dot(xr, yr) / denom)

def weekly_ic_table(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    feature_cols = ["past_total_momentum", "past_residual_momentum", "apwc", "apwc_rolling_z"]
    target_cols = ["future_total_return", "future_residual_return"]
    for feature in feature_cols:
        for target in target_cols:
            for gated_flag, g in [("all", panel), ("apwc_gate", panel[panel["apwc_gate"]])]:
                vals = []
                for _, h in g.groupby("analysis_date", sort=True):
                    x = h[feature].astype(float)
                    y = h[target].astype(float)
                    valid = x.notna() & y.notna()
                    if valid.sum() >= 3 and x.loc[valid].nunique() > 1 and y.loc[valid].nunique() > 1:
                        vals.append(fast_spearman_corr(x.loc[valid], y.loc[valid]))
                vals = pd.Series(vals, dtype=float).dropna()
                rows.append(
                    {
                        "feature": feature,
                        "target": target,
                        "sample": gated_flag,
                        "n_dates": int(len(vals)),
                        "mean_spearman_ic": float(vals.mean()) if len(vals) else np.nan,
                        "ic_t_stat": simple_t_stat(vals) if len(vals) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def weekly_predictive_regressions(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    data = panel.dropna(subset=["future_residual_return", "past_residual_momentum", "apwc_rolling_z"]).copy()
    if data.empty:
        return pd.DataFrame()
    data["apwc_gate_numeric"] = (data["apwc_rolling_z"] >= weekly_cfg.apwc_z_threshold).astype(float)
    data["interaction_gate_resid_mom"] = data["apwc_gate_numeric"] * data["past_residual_momentum"]
    data["interaction_z_resid_mom"] = data["apwc_rolling_z"] * data["past_residual_momentum"]
    specs = {
        "resid_momentum_only": ["past_residual_momentum"],
        "apwc_z_and_resid_momentum": ["past_residual_momentum", "apwc_rolling_z"],
        "gate_interaction": ["past_residual_momentum", "apwc_gate_numeric", "interaction_gate_resid_mom"],
        "z_interaction": ["past_residual_momentum", "apwc_rolling_z", "interaction_z_resid_mom"],
    }
    for name, xcols in specs.items():
        d = data.dropna(subset=xcols + ["future_residual_return"])
        if len(d) < len(xcols) + 3:
            rows.append({"model": name, "status": "too_few_obs", "n_obs": int(len(d))})
            continue
        x = sm.add_constant(d[xcols], has_constant="add")
        y = d["future_residual_return"].astype(float)
        model = sm.OLS(y, x).fit(cov_type="HC1")
        row = {"model": name, "status": "ok", "n_obs": int(model.nobs), "r_squared": float(model.rsquared)}
        for col in xcols:
            row[f"coef_{col}"] = float(model.params.get(col, np.nan))
            row[f"t_{col}"] = float(model.tvalues.get(col, np.nan))
        rows.append(row)
    return pd.DataFrame(rows)


def weekly_threshold_sweep(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    pieces = []
    if panel.empty:
        return pd.DataFrame()
    thresholds = sorted({float(strategy_cfg.apwc_z_threshold), 0.0, 1.0})
    max_top_n = max(1, min(2, int(panel.groupby("analysis_date")["theme_id"].nunique().max())))
    top_ns = [n for n in sorted({int(strategy_cfg.top_momentum_n), 1, 2}) if n <= max_top_n]
    for threshold in thresholds:
        for top_n in top_ns:
            strategy_panel, _ = build_weekly_strategy_returns(panel, strategy_cfg, apwc_z_threshold=threshold, top_n=top_n)
            summary = summarize_weekly_strategy(strategy_panel, strategy_cfg)
            summary["sweep_threshold"] = threshold
            summary["sweep_top_n"] = top_n
            pieces.append(summary)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def weekly_gate_diagnostics(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    return panel.groupby("analysis_date").agg(
        n_themes=("theme_id", "nunique"),
        n_gate=("apwc_gate", "sum"),
        gate_rate=("apwc_gate", "mean"),
        max_apwc_rolling_z=("apwc_rolling_z", "max"),
        mean_apwc=("apwc", "mean"),
        mean_future_residual_all=("future_residual_return", "mean"),
        mean_future_total_all=("future_total_return", "mean"),
    ).reset_index()



def rolling_z_weight_from_value(z: float, strategy_cfg: WeeklyMomentumConfig) -> float:
    """Soft APWC rolling-Z gate: 0 below threshold, 1 above high threshold."""
    if not np.isfinite(z):
        return 0.0
    low = float(strategy_cfg.apwc_z_threshold)
    high = float(strategy_cfg.rolling_z_soft_threshold_high)
    denom = max(high - low, 1e-12)
    return float(np.clip((float(z) - low) / denom, 0.0, 1.0))


def add_weekly_rrg_benchmark(
    panel: pd.DataFrame,
    return_col: str,
    benchmark_mode: str,
    date_col: str = "analysis_date",
) -> pd.DataFrame:
    """Benchmark-adjust weekly return input for RRG axes.

    For weekly rolling-Z validation this is intentionally generic: the same routine
    can be applied to residual momentum or total-return momentum.
    """
    out = panel.copy()
    x = out[return_col].astype(float)
    if benchmark_mode == "zero":
        bench = pd.Series(0.0, index=out.index)
    elif benchmark_mode == "cross_section_equal":
        bench = out.groupby(date_col)[return_col].transform("mean").astype(float)
    elif benchmark_mode == "cross_section_median":
        bench = out.groupby(date_col)[return_col].transform("median").astype(float)
    else:
        raise ValueError(f"Unknown weekly RRG benchmark_mode: {benchmark_mode}")
    out["weekly_rrg_benchmark_return"] = bench
    out["weekly_rrg_relative_return"] = x - bench
    out["weekly_rrg_benchmark_mode"] = benchmark_mode
    return out


def add_weekly_rrg_axes(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
    rrg_cfg: RRGConfig,
    standardization: str,
    date_col: str = "analysis_date",
) -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["rrg_rs_momentum_raw"] = out.groupby("theme_id")["weekly_rrg_relative_return"].diff(rrg_cfg.rs_momentum_lag_periods)

    if standardization == "time_series":
        out["rrg_rs_ratio_z"] = out.groupby("theme_id", group_keys=False)["weekly_rrg_relative_return"].apply(
            lambda s: zscore_against_prior_history(s, rrg_cfg.standardization_lookback, rrg_cfg.standardization_min_periods)
        )
        out["rrg_rs_momentum_z"] = out.groupby("theme_id", group_keys=False)["rrg_rs_momentum_raw"].apply(
            lambda s: zscore_against_prior_history(s, rrg_cfg.standardization_lookback, rrg_cfg.standardization_min_periods)
        )
    elif standardization == "cross_sectional":
        out["rrg_rs_ratio_z"] = cross_sectional_zscore(out, "weekly_rrg_relative_return", date_col=date_col)
        out["rrg_rs_momentum_z"] = cross_sectional_zscore(out, "rrg_rs_momentum_raw", date_col=date_col)
    elif standardization == "expanding_time_series":
        out["rrg_rs_ratio_z"] = out.groupby("theme_id", group_keys=False)["weekly_rrg_relative_return"].apply(
            lambda s: (s - s.shift(1).expanding(rrg_cfg.standardization_min_periods).mean())
            / s.shift(1).expanding(rrg_cfg.standardization_min_periods).std(ddof=1).replace(0.0, np.nan)
        )
        out["rrg_rs_momentum_z"] = out.groupby("theme_id", group_keys=False)["rrg_rs_momentum_raw"].apply(
            lambda s: (s - s.shift(1).expanding(rrg_cfg.standardization_min_periods).mean())
            / s.shift(1).expanding(rrg_cfg.standardization_min_periods).std(ddof=1).replace(0.0, np.nan)
        )
    else:
        raise ValueError(f"Unknown weekly RRG standardization: {standardization}")

    out["weekly_rrg_standardization"] = standardization
    out["rs_ratio"] = rrg_cfg.rs_ratio_center + rrg_cfg.rs_ratio_scale * out["rrg_rs_ratio_z"]
    out["rs_momentum"] = rrg_cfg.rs_ratio_center + rrg_cfg.rs_ratio_scale * out["rrg_rs_momentum_z"]
    return out


def add_weekly_rrg_quadrants_and_transitions(panel: pd.DataFrame, rrg_cfg: RRGConfig, date_col: str = "analysis_date") -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["rrg_quadrant"] = [
        classify_rrg_quadrant(x, y, center=rrg_cfg.rs_ratio_center)
        for x, y in zip(out["rs_ratio"], out["rs_momentum"])
    ]
    out["prior_rrg_quadrant"] = out.groupby("theme_id")["rrg_quadrant"].shift(1)
    out["rrg_transition"] = out["prior_rrg_quadrant"].fillna("Start") + " -> " + out["rrg_quadrant"].astype(str)
    out["rrg_quadrant_direction"] = out["rrg_quadrant"].map(direction_from_rrg_quadrant).fillna(0).astype(int)

    def _transition_direction(row: pd.Series) -> int:
        prev_q, q = row["prior_rrg_quadrant"], row["rrg_quadrant"]
        if q == "Leading" or (prev_q == "Improving" and q == "Leading"):
            return 1
        if q == "Lagging" or (prev_q == "Weakening" and q == "Lagging"):
            return -1
        return 0

    out["rrg_transition_direction"] = out.apply(_transition_direction, axis=1).astype(int)
    return out


def add_weekly_rolling_z_coherence_rrg(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig, date_col: str = "analysis_date") -> pd.DataFrame:
    out = panel.sort_values(["theme_id", date_col]).copy()
    out["rolling_z_coherence_x"] = out["apwc_rolling_z"].astype(float)
    out["rolling_z_delta"] = out.groupby("theme_id")["rolling_z_coherence_x"].diff()
    out["rolling_z_gate"] = out["rolling_z_coherence_x"] >= strategy_cfg.apwc_z_threshold
    out["rolling_z_weight"] = out["rolling_z_coherence_x"].map(lambda z: rolling_z_weight_from_value(z, strategy_cfg))

    def _state(row: pd.Series) -> str:
        z = row["rolling_z_coherence_x"]
        dz = row["rolling_z_delta"]
        if not np.isfinite(z):
            return "Undefined"
        if not np.isfinite(dz):
            return "Coherence high" if z >= strategy_cfg.apwc_z_threshold else "Unconfirmed"
        if z >= strategy_cfg.apwc_z_threshold and dz >= 0:
            return "Coherence leading"
        if z >= strategy_cfg.apwc_z_threshold and dz < 0:
            return "Coherence weakening"
        if z < strategy_cfg.apwc_z_threshold and dz >= 0:
            return "Coherence improving"
        return "Coherence lagging"

    out["rolling_z_coherence_state"] = out.apply(_state, axis=1)
    out["rolling_z_lifecycle_weight"] = out["rolling_z_coherence_state"].map(
        {
            "Coherence leading": 1.00,
            "Coherence high": 0.75,
            "Coherence weakening": 0.50,
            "Coherence improving": 0.25,
            "Coherence lagging": 0.00,
            "Unconfirmed": 0.00,
            "Undefined": 0.00,
        }
    ).fillna(0.0).astype(float)
    return out


def add_weekly_rrg_signal_patterns(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig, rrg_cfg: RRGConfig) -> pd.DataFrame:
    out = panel.copy()
    out["weekly_rrg_raw_score"] = (
        rrg_cfg.alpha_ratio * out["rrg_rs_ratio_z"].astype(float)
        + rrg_cfg.beta_momentum * out["rrg_rs_momentum_z"].astype(float)
    )
    out["weekly_rrg_gate"] = out["rolling_z_gate"].fillna(False).astype(bool)

    def _pattern_a(row: pd.Series) -> str:
        if not bool(row["weekly_rrg_gate"]):
            return "no_position_not_in_rolling_z_regime"
        q = row["rrg_quadrant"]
        prev_q = row["prior_rrg_quadrant"]
        if q == "Leading" or (prev_q == "Improving" and q == "Leading"):
            return "long"
        if q == "Lagging" or (prev_q == "Weakening" and q == "Lagging"):
            return "underweight_or_short"
        if q == "Weakening":
            return "hold_or_reduce"
        if q == "Improving":
            return "watchlist"
        return "no_position_rrg_undefined"

    out["weekly_pattern_a_signal"] = out.apply(_pattern_a, axis=1)
    out["weekly_pattern_a_position"] = out["weekly_pattern_a_signal"].map(
        {"long": 1, "underweight_or_short": -1, "hold_or_reduce": 0, "watchlist": 0}
    ).fillna(0).astype(int)

    out["weekly_pattern_b_score_hard_gate"] = out["weekly_rrg_raw_score"].fillna(0.0) * out["weekly_rrg_gate"].astype(float)
    out["weekly_pattern_b_score_soft_gate"] = out["weekly_rrg_raw_score"].fillna(0.0) * out["rolling_z_weight"].astype(float)
    out["weekly_pattern_b_position_hard"] = out["weekly_pattern_b_score_hard_gate"].map(_safe_sign)
    out["weekly_pattern_b_position_soft"] = out["weekly_pattern_b_score_soft_gate"].map(_safe_sign)

    out["weekly_pattern_c_score"] = out["weekly_rrg_gate"].astype(float) * out["rrg_transition_direction"].astype(float)
    out["weekly_pattern_c_position"] = out["weekly_pattern_c_score"].map(_safe_sign)

    out["weekly_two_layer_score"] = (
        out["rolling_z_weight"].astype(float)
        * out["rolling_z_lifecycle_weight"].astype(float)
        * out["weekly_rrg_raw_score"].fillna(0.0)
    )
    out["weekly_two_layer_position"] = out["weekly_two_layer_score"].map(_safe_sign)
    return out


def build_weekly_rrg_suite(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
    rrg_cfg: RRGConfig,
) -> dict[str, pd.DataFrame]:
    if panel.empty:
        return {}
    panels: dict[str, pd.DataFrame] = {}
    return_specs = {
        "residual": ("past_residual_momentum", "future_residual_return"),
        "total": ("past_total_momentum", "future_total_return"),
    }
    base_cols = [
        "mode",
        "theme_id",
        "theme_name",
        "analysis_date",
        "rebalance_date",
        "next_rebalance_date",
        "past_start",
        "past_end",
        "future_start",
        "future_end",
        "n_members",
        "apwc",
        "apwc_rolling_z",
        "apwc_gate",
        "past_total_momentum",
        "past_residual_momentum",
        "future_total_return",
        "future_residual_return",
    ]
    base = panel[[c for c in base_cols if c in panel.columns]].copy()
    for return_mode in strategy_cfg.rrg_return_modes:
        if return_mode not in return_specs:
            continue
        past_col, future_col = return_specs[return_mode]
        for benchmark_mode in strategy_cfg.rrg_benchmark_modes:
            b = add_weekly_rrg_benchmark(base, return_col=past_col, benchmark_mode=benchmark_mode)
            b["weekly_rrg_return_mode"] = return_mode
            b["weekly_rrg_past_return_col"] = past_col
            b["weekly_rrg_future_return_col"] = future_col
            b["weekly_rrg_future_return"] = b[future_col].astype(float)
            for standardization in strategy_cfg.rrg_standardizations:
                p = add_weekly_rrg_axes(b, strategy_cfg=strategy_cfg, rrg_cfg=rrg_cfg, standardization=standardization)
                p = add_weekly_rrg_quadrants_and_transitions(p, rrg_cfg=rrg_cfg)
                p = add_weekly_rolling_z_coherence_rrg(p, strategy_cfg=strategy_cfg)
                p = add_weekly_rrg_signal_patterns(p, strategy_cfg=strategy_cfg, rrg_cfg=rrg_cfg)
                key = f"{return_mode}__{benchmark_mode}__{standardization}"
                p["weekly_rrg_panel"] = key
                panels[key] = p.sort_values(["analysis_date", "theme_id"]).reset_index(drop=True)
    return panels


def summarize_weekly_rrg_panel(panel: pd.DataFrame, panel_name: str) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    position_specs = [
        ("weekly_pattern_a_quadrant", "weekly_pattern_a_position"),
        ("weekly_pattern_b_hard_gate", "weekly_pattern_b_position_hard"),
        ("weekly_pattern_b_soft_gate", "weekly_pattern_b_position_soft"),
        ("weekly_pattern_c_transition", "weekly_pattern_c_position"),
        ("weekly_two_layer", "weekly_two_layer_position"),
    ]
    for method, position_col in position_specs:
        p = panel.copy()
        p["position"] = p[position_col].astype(float)
        p["signed_future_primary"] = p["position"] * p["weekly_rrg_future_return"].astype(float)
        p["signed_future_residual"] = p["position"] * p["future_residual_return"].astype(float)
        p["signed_future_total"] = p["position"] * p["future_total_return"].astype(float)
        invested = p[p["position"].abs() > 0]
        rows.append(
            {
                "weekly_rrg_panel": panel_name,
                "return_mode": p["weekly_rrg_return_mode"].iloc[0],
                "benchmark_mode": p["weekly_rrg_benchmark_mode"].iloc[0],
                "standardization": p["weekly_rrg_standardization"].iloc[0],
                "method": method,
                "rows": int(len(p)),
                "invested_rows": int(len(invested)),
                "long_rows": int((p["position"] > 0).sum()),
                "short_rows": int((p["position"] < 0).sum()),
                "invested_rate": float((p["position"].abs() > 0).mean()) if len(p) else np.nan,
                "mean_signed_future_primary": float(invested["signed_future_primary"].mean()) if len(invested) else np.nan,
                "t_signed_future_primary": simple_t_stat(invested["signed_future_primary"]) if len(invested) else np.nan,
                "mean_signed_future_residual": float(invested["signed_future_residual"].mean()) if len(invested) else np.nan,
                "t_signed_future_residual": simple_t_stat(invested["signed_future_residual"]) if len(invested) else np.nan,
                "mean_signed_future_total": float(invested["signed_future_total"].mean()) if len(invested) else np.nan,
                "t_signed_future_total": simple_t_stat(invested["signed_future_total"]) if len(invested) else np.nan,
                "win_rate_when_invested": float((invested["signed_future_primary"] > 0).mean()) if len(invested) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def weekly_rrg_quadrant_forward_return_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for key, panel in panels.items():
        if panel.empty:
            continue
        for sample_name, g in [("all", panel), ("rolling_z_gate", panel[panel["weekly_rrg_gate"]])]:
            for quadrant, h in g.groupby("rrg_quadrant", dropna=False, sort=True):
                signed_primary = h["rrg_quadrant_direction"].astype(float) * h["weekly_rrg_future_return"].astype(float)
                rows.append(
                    {
                        "weekly_rrg_panel": key,
                        "return_mode": panel["weekly_rrg_return_mode"].iloc[0],
                        "sample": sample_name,
                        "rrg_quadrant": str(quadrant),
                        "n_obs": int(len(h)),
                        "mean_future_primary": float(h["weekly_rrg_future_return"].mean()) if len(h) else np.nan,
                        "t_future_primary": simple_t_stat(h["weekly_rrg_future_return"]) if len(h) else np.nan,
                        "mean_signed_by_quadrant_direction": float(signed_primary.mean()) if len(h) else np.nan,
                        "t_signed_by_quadrant_direction": simple_t_stat(signed_primary) if len(h) else np.nan,
                        "mean_future_residual": float(h["future_residual_return"].mean()) if len(h) else np.nan,
                        "mean_future_total": float(h["future_total_return"].mean()) if len(h) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def weekly_rrg_transition_forward_return_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for key, panel in panels.items():
        if panel.empty:
            continue
        for sample_name, g in [("all", panel), ("rolling_z_gate", panel[panel["weekly_rrg_gate"]])]:
            for transition, h in g.groupby("rrg_transition", dropna=False, sort=True):
                if len(h) == 0:
                    continue
                signed_primary = h["rrg_transition_direction"].astype(float) * h["weekly_rrg_future_return"].astype(float)
                rows.append(
                    {
                        "weekly_rrg_panel": key,
                        "return_mode": panel["weekly_rrg_return_mode"].iloc[0],
                        "sample": sample_name,
                        "rrg_transition": str(transition),
                        "n_obs": int(len(h)),
                        "mean_future_primary": float(h["weekly_rrg_future_return"].mean()),
                        "t_future_primary": simple_t_stat(h["weekly_rrg_future_return"]),
                        "mean_signed_by_transition_direction": float(signed_primary.mean()),
                        "t_signed_by_transition_direction": simple_t_stat(signed_primary),
                        "mean_future_residual": float(h["future_residual_return"].mean()),
                        "mean_future_total": float(h["future_total_return"].mean()),
                    }
                )
    return pd.DataFrame(rows)


def weekly_rrg_ic_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    feature_cols = [
        "apwc_rolling_z",
        "rolling_z_delta",
        "rrg_rs_ratio_z",
        "rrg_rs_momentum_z",
        "weekly_rrg_raw_score",
        "weekly_pattern_b_score_soft_gate",
        "weekly_two_layer_score",
    ]
    target_cols = ["weekly_rrg_future_return", "future_residual_return", "future_total_return"]
    preferred_keys = [k for k in ("residual__zero__time_series", "total__zero__time_series") if k in panels]
    if not preferred_keys:
        preferred_keys = list(panels.keys())[:2]
    for key in preferred_keys:
        panel = panels[key]
        for sample_name, g in [("all", panel), ("rolling_z_gate", panel[panel["weekly_rrg_gate"]])]:
            for feature in feature_cols:
                for target in target_cols:
                    vals = []
                    for _, h in g.groupby("analysis_date", sort=True):
                        x = h[feature].astype(float)
                        y = h[target].astype(float)
                        valid = x.notna() & y.notna()
                        if valid.sum() >= 3 and x.loc[valid].nunique() > 1 and y.loc[valid].nunique() > 1:
                            vals.append(fast_spearman_corr(x.loc[valid], y.loc[valid]))
                    vals = pd.Series(vals, dtype=float).dropna()
                    rows.append(
                        {
                            "weekly_rrg_panel": key,
                            "return_mode": panel["weekly_rrg_return_mode"].iloc[0],
                            "sample": sample_name,
                            "feature": feature,
                            "target": target,
                            "n_dates": int(len(vals)),
                            "mean_spearman_ic": float(vals.mean()) if len(vals) else np.nan,
                            "ic_t_stat": simple_t_stat(vals) if len(vals) else np.nan,
                        }
                    )
    return pd.DataFrame(rows)


def _weights_from_selected(selected: pd.DataFrame, side_col: str = "position") -> pd.Series:
    if selected.empty:
        return pd.Series(dtype=float)
    pos = selected[side_col].astype(float)
    longs = selected.index[pos > 0]
    shorts = selected.index[pos < 0]
    weights = pd.Series(0.0, index=selected.index, dtype=float)
    if len(longs) and len(shorts):
        weights.loc[longs] = 0.5 / len(longs)
        weights.loc[shorts] = -0.5 / len(shorts)
    elif len(longs):
        weights.loc[longs] = 1.0 / len(longs)
    elif len(shorts):
        weights.loc[shorts] = -1.0 / len(shorts)
    return weights


def build_weekly_rrg_portfolio_returns(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
    apwc_z_threshold: float | None = None,
    top_n: int | None = None,
    cost_bps: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    if apwc_z_threshold is None:
        apwc_z_threshold = strategy_cfg.apwc_z_threshold
    if top_n is None:
        top_n = strategy_cfg.top_momentum_n

    method_specs = [
        ("weekly_rrg_soft_score_long_only", "weekly_pattern_b_score_soft_gate", "score_long_only"),
        ("weekly_rrg_hard_score_long_only", "weekly_pattern_b_score_hard_gate", "score_long_only"),
        ("weekly_rrg_two_layer_long_only", "weekly_two_layer_score", "score_long_only"),
        ("weekly_rrg_quadrant_long_short", "weekly_pattern_a_position", "position_long_short"),
        ("weekly_rrg_transition_long_short", "weekly_pattern_c_position", "position_long_short"),
    ]
    rows = []
    selection_rows = []
    prev_weights_by_method: dict[str, pd.Series] = {}
    for analysis_date, g in panel.groupby("analysis_date", sort=True):
        base_candidates = g.dropna(subset=["weekly_rrg_future_return", "future_residual_return", "future_total_return"]).copy()
        base_candidates = base_candidates[base_candidates["apwc_rolling_z"].fillna(-np.inf) >= apwc_z_threshold]
        for method, score_or_pos_col, mode in method_specs:
            candidates = base_candidates.copy()
            if mode == "score_long_only":
                candidates = candidates.dropna(subset=[score_or_pos_col])
                candidates = candidates[candidates[score_or_pos_col] > 0].sort_values(score_or_pos_col, ascending=False).head(top_n)
                candidates["position"] = 1.0
                sort_col = score_or_pos_col
            else:
                candidates = candidates.dropna(subset=[score_or_pos_col])
                candidates["position"] = candidates[score_or_pos_col].astype(float)
                candidates = candidates[candidates["position"].abs() > 0]
                candidates["abs_rrg_score"] = candidates["weekly_rrg_raw_score"].abs()
                candidates = candidates.sort_values("abs_rrg_score", ascending=False).head(max(1, top_n * 2))
                sort_col = "abs_rrg_score"
            if not candidates.empty:
                weights = _weights_from_selected(candidates, side_col="position")
                candidates = candidates.copy()
                candidates["portfolio_weight"] = weights
            else:
                weights = pd.Series(dtype=float)

            theme_weights = pd.Series(weights.to_numpy(), index=candidates["theme_id"].to_numpy(), dtype=float) if not candidates.empty else pd.Series(dtype=float)
            prior = prev_weights_by_method.get(method, pd.Series(dtype=float))
            all_theme_ids = prior.index.union(theme_weights.index)
            turnover = float((theme_weights.reindex(all_theme_ids, fill_value=0.0) - prior.reindex(all_theme_ids, fill_value=0.0)).abs().sum() * 0.5)
            prev_weights_by_method[method] = theme_weights

            gross_primary = float((candidates["portfolio_weight"] * candidates["weekly_rrg_future_return"]).sum()) if not candidates.empty else 0.0
            gross_residual = float((candidates["portfolio_weight"] * candidates["future_residual_return"]).sum()) if not candidates.empty else 0.0
            gross_total = float((candidates["portfolio_weight"] * candidates["future_total_return"]).sum()) if not candidates.empty else 0.0
            cost = float(cost_bps) / 10000.0 * turnover
            row = {
                "strategy": method,
                "weekly_rrg_panel": panel["weekly_rrg_panel"].iloc[0],
                "return_mode": panel["weekly_rrg_return_mode"].iloc[0],
                "benchmark_mode": panel["weekly_rrg_benchmark_mode"].iloc[0],
                "standardization": panel["weekly_rrg_standardization"].iloc[0],
                "analysis_date": pd.Timestamp(analysis_date),
                "apwc_z_threshold": float(apwc_z_threshold),
                "top_n": int(top_n),
                "cost_bps": float(cost_bps),
                "n_selected": int(len(candidates)),
                "invested": bool(len(candidates) > 0),
                "turnover": turnover,
                "transaction_cost": cost,
                "gross_primary_return": gross_primary,
                "net_primary_return": gross_primary - cost,
                "gross_residual_return": gross_residual,
                "net_residual_return": gross_residual - cost,
                "gross_total_return": gross_total,
                "net_total_return": gross_total - cost,
            }
            rows.append(row)
            if not candidates.empty:
                tmp = candidates.copy()
                tmp["strategy"] = method
                tmp["apwc_z_threshold"] = float(apwc_z_threshold)
                tmp["top_n"] = int(top_n)
                tmp["cost_bps"] = float(cost_bps)
                tmp["rank_sort_col"] = sort_col
                selection_rows.append(tmp)
    return pd.DataFrame(rows), pd.concat(selection_rows, ignore_index=True) if selection_rows else pd.DataFrame()


def summarize_weekly_rrg_portfolio(strategy_panel: pd.DataFrame) -> pd.DataFrame:
    if strategy_panel.empty:
        return pd.DataFrame()
    rows = []
    group_cols = ["weekly_rrg_panel", "strategy", "apwc_z_threshold", "top_n", "cost_bps"]
    for keys, g in strategy_panel.groupby(group_cols, sort=True):
        panel_name, strategy, threshold, top_n, cost_bps = keys
        net_primary = g["net_primary_return"].astype(float)
        net_residual = g["net_residual_return"].astype(float)
        net_total = g["net_total_return"].astype(float)
        rows.append(
            {
                "weekly_rrg_panel": panel_name,
                "strategy": strategy,
                "return_mode": g["return_mode"].iloc[0],
                "benchmark_mode": g["benchmark_mode"].iloc[0],
                "standardization": g["standardization"].iloc[0],
                "apwc_z_threshold": float(threshold),
                "top_n": int(top_n),
                "cost_bps": float(cost_bps),
                "n_weeks": int(len(g)),
                "n_invested_weeks": int(g["invested"].sum()),
                "invested_rate": float(g["invested"].mean()) if len(g) else np.nan,
                "avg_turnover": float(g["turnover"].mean()) if len(g) else np.nan,
                "mean_net_primary_return": float(net_primary.mean()) if len(g) else np.nan,
                "t_net_primary_return": simple_t_stat(net_primary),
                "mean_net_residual_return": float(net_residual.mean()) if len(g) else np.nan,
                "t_net_residual_return": simple_t_stat(net_residual),
                "mean_net_total_return": float(net_total.mean()) if len(g) else np.nan,
                "t_net_total_return": simple_t_stat(net_total),
                "win_rate_net_primary": float((net_primary > 0).mean()) if len(g) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def weekly_rrg_threshold_topn_sweep(
    panels: dict[str, pd.DataFrame],
    strategy_cfg: WeeklyMomentumConfig,
    panel_keys: list[str] | None = None,
) -> pd.DataFrame:
    if not panels:
        return pd.DataFrame()
    if panel_keys is None:
        preferred = ["residual__zero__time_series"]
        panel_keys = [k for k in preferred if k in panels]
    pieces = []
    # A compact sweep is enough for the notebook smoke run; users can expand these grids in production.
    sweep_thresholds = tuple(dict.fromkeys([strategy_cfg.apwc_z_threshold, 1.0, 2.0]))
    sweep_top_n = tuple(n for n in strategy_cfg.top_n_grid if n <= 2) or (strategy_cfg.top_momentum_n,)
    for key in panel_keys:
        panel = panels[key]
        for threshold in sweep_thresholds:
            for top_n in sweep_top_n:
                strat, _ = build_weekly_rrg_portfolio_returns(panel, strategy_cfg, apwc_z_threshold=threshold, top_n=top_n, cost_bps=0.0)
                summary = summarize_weekly_rrg_portfolio(strat)
                summary["sweep_threshold"] = float(threshold)
                summary["sweep_top_n"] = int(top_n)
                pieces.append(summary)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def weekly_rrg_turnover_cost_stress(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
) -> pd.DataFrame:
    """Transaction-cost stress using one base portfolio path, not one rebuild per cost level."""
    if panel.empty:
        return pd.DataFrame()
    base_strategy, _ = build_weekly_rrg_portfolio_returns(panel, strategy_cfg, cost_bps=0.0)
    if base_strategy.empty:
        return pd.DataFrame()
    pieces = []
    for cost_bps in strategy_cfg.transaction_cost_bps_grid:
        g = base_strategy.copy()
        cost = g["turnover"].astype(float) * float(cost_bps) / 10000.0
        g["cost_bps"] = float(cost_bps)
        g["transaction_cost"] = cost
        g["net_primary_return"] = g["gross_primary_return"].astype(float) - cost
        g["net_residual_return"] = g["gross_residual_return"].astype(float) - cost
        g["net_total_return"] = g["gross_total_return"].astype(float) - cost
        pieces.append(g)
    return summarize_weekly_rrg_portfolio(pd.concat(pieces, ignore_index=True))


def weekly_rrg_predictive_regressions(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    rows = []
    if panel.empty:
        return pd.DataFrame()
    data = panel.dropna(
        subset=[
            "weekly_rrg_future_return",
            "apwc_rolling_z",
            "rolling_z_delta",
            "rrg_rs_ratio_z",
            "rrg_rs_momentum_z",
            "weekly_rrg_raw_score",
            "weekly_pattern_b_score_soft_gate",
        ]
    ).copy()
    if data.empty:
        return pd.DataFrame()
    data["rolling_z_gate_numeric"] = (data["apwc_rolling_z"] >= strategy_cfg.apwc_z_threshold).astype(float)
    data["interaction_gate_rrg_score"] = data["rolling_z_gate_numeric"] * data["weekly_rrg_raw_score"]
    data["interaction_z_rrg_score"] = data["apwc_rolling_z"] * data["weekly_rrg_raw_score"]
    specs = {
        "rrg_score_only": ["weekly_rrg_raw_score"],
        "rolling_z_plus_rrg": ["apwc_rolling_z", "weekly_rrg_raw_score"],
        "rrg_axes_plus_rolling_z": ["apwc_rolling_z", "rolling_z_delta", "rrg_rs_ratio_z", "rrg_rs_momentum_z"],
        "gate_rrg_interaction": ["rolling_z_gate_numeric", "weekly_rrg_raw_score", "interaction_gate_rrg_score"],
        "z_rrg_interaction": ["apwc_rolling_z", "weekly_rrg_raw_score", "interaction_z_rrg_score"],
    }
    for target in ["weekly_rrg_future_return", "future_residual_return", "future_total_return"]:
        for name, xcols in specs.items():
            d = data.dropna(subset=xcols + [target])
            if len(d) < len(xcols) + 5:
                rows.append({"target": target, "model": name, "status": "too_few_obs", "n_obs": int(len(d))})
                continue
            x = sm.add_constant(d[xcols], has_constant="add")
            y = d[target].astype(float)
            try:
                model = sm.OLS(y, x).fit(cov_type="HC1")
                row = {"target": target, "model": name, "status": "ok", "n_obs": int(model.nobs), "r_squared": float(model.rsquared)}
                for col in xcols:
                    row[f"coef_{col}"] = float(model.params.get(col, np.nan))
                    row[f"t_{col}"] = float(model.tvalues.get(col, np.nan))
                rows.append(row)
            except Exception as exc:
                rows.append({"target": target, "model": name, "status": f"failed: {exc}", "n_obs": int(len(d))})
    return pd.DataFrame(rows)


def weekly_rrg_placebo_gate_test(
    panel: pd.DataFrame,
    strategy_cfg: WeeklyMomentumConfig,
    n_reps: int | None = None,
) -> pd.DataFrame:
    """Fast placebo test for the weekly rolling-Z gate used inside RRG.

    The null shuffles APWC rolling-Z values cross-sectionally within each rebalance date,
    preserving the date-level opportunity set and the RRG return axes.  To keep this test
    usable in notebooks, it evaluates the primary soft-score long-only leg directly rather
    than rebuilding the full portfolio object for every placebo replicate.
    """
    if panel.empty:
        return pd.DataFrame()
    if n_reps is None:
        n_reps = min(int(strategy_cfg.rrg_placebo_reps), 20)
    else:
        n_reps = min(int(n_reps), 20)

    actual_strategy, _ = build_weekly_rrg_portfolio_returns(panel, strategy_cfg, cost_bps=0.0)
    actual_summary = summarize_weekly_rrg_portfolio(actual_strategy)
    target_strategy = "weekly_rrg_soft_score_long_only"
    actual = actual_summary[actual_summary["strategy"].eq(target_strategy)]
    if actual.empty:
        return pd.DataFrame()

    actual_mean = float(actual["mean_net_primary_return"].iloc[0])
    actual_residual_mean = float(actual["mean_net_residual_return"].iloc[0]) if "mean_net_residual_return" in actual else np.nan

    required = ["analysis_date", "apwc_rolling_z", "weekly_rrg_raw_score", "weekly_rrg_future_return", "future_residual_return"]
    missing = [c for c in required if c not in panel.columns]
    if missing:
        return pd.DataFrame([{"status": f"missing_columns: {missing}", "weekly_rrg_panel": panel.get("weekly_rrg_panel", pd.Series([""])).iloc[0]}])

    rng = np.random.default_rng(cfg.seed + 404)
    date_groups = [(d, g.copy()) for d, g in panel.groupby("analysis_date", sort=False)]
    placebo_primary_means: list[float] = []
    placebo_residual_means: list[float] = []
    invested_rates: list[float] = []

    for _ in range(int(n_reps)):
        primary_returns: list[float] = []
        residual_returns: list[float] = []
        invested_flags: list[int] = []
        for _, g in date_groups:
            g = g.dropna(subset=["weekly_rrg_raw_score", "weekly_rrg_future_return", "future_residual_return"])
            if g.empty:
                primary_returns.append(0.0)
                residual_returns.append(0.0)
                invested_flags.append(0)
                continue
            zvals = g["apwc_rolling_z"].to_numpy(dtype=float, copy=True)
            rng.shuffle(zvals)
            # Soft coherence weight induced by the shuffled APWC rolling-Z gate.
            roll_weight = np.array([rolling_z_weight_from_value(z, strategy_cfg) for z in zvals], dtype=float)
            raw_score = g["weekly_rrg_raw_score"].to_numpy(dtype=float)
            placebo_score = roll_weight * raw_score
            tmp = g.copy()
            tmp["_placebo_score"] = placebo_score
            tmp = tmp[tmp["_placebo_score"] > strategy_cfg.rrg_score_threshold]
            if tmp.empty:
                primary_returns.append(0.0)
                residual_returns.append(0.0)
                invested_flags.append(0)
            else:
                selected = tmp.sort_values("_placebo_score", ascending=False).head(strategy_cfg.top_momentum_n)
                primary_returns.append(float(selected["weekly_rrg_future_return"].mean()))
                residual_returns.append(float(selected["future_residual_return"].mean()))
                invested_flags.append(1)
        placebo_primary_means.append(float(np.mean(primary_returns)) if primary_returns else np.nan)
        placebo_residual_means.append(float(np.mean(residual_returns)) if residual_returns else np.nan)
        invested_rates.append(float(np.mean(invested_flags)) if invested_flags else np.nan)

    placebo_primary = pd.Series(placebo_primary_means, dtype=float).dropna()
    placebo_residual = pd.Series(placebo_residual_means, dtype=float).dropna()
    placebo_invested = pd.Series(invested_rates, dtype=float).dropna()
    return pd.DataFrame(
        [
            {
                "weekly_rrg_panel": panel["weekly_rrg_panel"].iloc[0] if "weekly_rrg_panel" in panel.columns else "",
                "strategy": target_strategy,
                "n_reps": int(len(placebo_primary)),
                "actual_mean_net_primary_return": actual_mean,
                "placebo_mean": float(placebo_primary.mean()) if len(placebo_primary) else np.nan,
                "placebo_std": float(placebo_primary.std(ddof=1)) if len(placebo_primary) > 1 else np.nan,
                "empirical_p_value_one_sided": float(((placebo_primary >= actual_mean).sum() + 1) / (len(placebo_primary) + 1)) if len(placebo_primary) else np.nan,
                "placebo_95pct": float(placebo_primary.quantile(0.95)) if len(placebo_primary) else np.nan,
                "actual_mean_net_residual_return": actual_residual_mean,
                "placebo_residual_mean": float(placebo_residual.mean()) if len(placebo_residual) else np.nan,
                "placebo_residual_std": float(placebo_residual.std(ddof=1)) if len(placebo_residual) > 1 else np.nan,
                "empirical_p_value_residual_one_sided": float(((placebo_residual >= actual_residual_mean).sum() + 1) / (len(placebo_residual) + 1)) if len(placebo_residual) and np.isfinite(actual_residual_mean) else np.nan,
                "placebo_residual_95pct": float(placebo_residual.quantile(0.95)) if len(placebo_residual) else np.nan,
                "placebo_invested_rate_mean": float(placebo_invested.mean()) if len(placebo_invested) else np.nan,
            }
        ]
    )

def weekly_rrg_walk_forward_validation(panel: pd.DataFrame, strategy_cfg: WeeklyMomentumConfig) -> pd.DataFrame:
    """Fast walk-forward check for the default weekly rolling-Z RRG rule.

    This validates time separation without re-optimizing a large hyperparameter grid.
    Production research can expand the grid; the notebook keeps this lightweight.
    """
    if panel.empty:
        return pd.DataFrame()
    dates = pd.Index(panel["analysis_date"].drop_duplicates().sort_values())
    if len(dates) < 10:
        return pd.DataFrame([{"status": "too_few_dates", "n_dates": int(len(dates))}])
    split_idx = int(np.floor(len(dates) * strategy_cfg.walkforward_train_fraction))
    split_idx = min(max(split_idx, 3), len(dates) - 3)
    splits = {"train": set(dates[:split_idx]), "test": set(dates[split_idx:])}
    rows = []
    threshold = float(strategy_cfg.apwc_z_threshold)
    top_n = int(strategy_cfg.top_momentum_n)
    for period, date_set in splits.items():
        returns = []
        residual_returns = []
        invested = []
        sub = panel[panel["analysis_date"].isin(date_set)].copy()
        for _, g in sub.groupby("analysis_date", sort=True):
            candidates = g[(g["apwc_rolling_z"].astype(float) >= threshold) & (g["weekly_pattern_b_score_soft_gate"].astype(float) > strategy_cfg.rrg_score_threshold)]
            selected = candidates.sort_values("weekly_pattern_b_score_soft_gate", ascending=False).head(top_n)
            returns.append(float(selected["future_total_return"].mean()) if not selected.empty else 0.0)
            residual_returns.append(float(selected["future_residual_return"].mean()) if not selected.empty else 0.0)
            invested.append(bool(not selected.empty))
        ret = pd.Series(returns, dtype=float)
        resid = pd.Series(residual_returns, dtype=float)
        rows.append(
            {
                "status": "ok",
                "period": period,
                "threshold": threshold,
                "top_n": top_n,
                "n_weeks": int(len(ret)),
                "invested_rate": float(np.mean(invested)) if invested else np.nan,
                "mean_return": float(ret.mean()) if len(ret) else np.nan,
                "return_t": simple_t_stat(ret),
                "mean_residual_return": float(resid.mean()) if len(resid) else np.nan,
                "residual_t": simple_t_stat(resid),
                "train_end_date": pd.Timestamp(dates[split_idx - 1]),
                "test_start_date": pd.Timestamp(dates[split_idx]),
                "selected_by": "fixed_default_parameters_fast_check",
            }
        )
    return pd.DataFrame(rows)


def weekly_rrg_mosaic_gate_overlap(panel: pd.DataFrame, mosaic_results: pd.DataFrame, mosaic_z_threshold: float = 2.0, rolling_z_threshold: float = 0.0) -> pd.DataFrame:
    if panel.empty or mosaic_results.empty or "z_score" not in mosaic_results.columns:
        return pd.DataFrame()
    rows = []
    z_source = mosaic_results[["theme_id", "analysis_date", "z_score"]].dropna().copy()
    z_source = z_source.sort_values(["theme_id", "analysis_date"])
    for theme_id, g in panel.groupby("theme_id", sort=True):
        z = z_source[z_source["theme_id"].eq(theme_id)].sort_values("analysis_date")
        if z.empty:
            tmp = g.copy()
            tmp["latest_mosaic_z_score"] = np.nan
        else:
            tmp = pd.merge_asof(
                g.sort_values("analysis_date"),
                z[["analysis_date", "z_score"]].sort_values("analysis_date"),
                on="analysis_date",
                direction="backward",
            ).rename(columns={"z_score": "latest_mosaic_z_score"})
            tmp["theme_id"] = theme_id
        rows.append(tmp)
    merged = pd.concat(rows, ignore_index=True)
    merged["mosaic_gate"] = merged["latest_mosaic_z_score"] >= mosaic_z_threshold
    merged["rolling_z_gate"] = merged["apwc_rolling_z"] >= rolling_z_threshold
    out = merged.groupby(["mosaic_gate", "rolling_z_gate"], dropna=False).agg(
        n_obs=("theme_id", "size"),
        n_themes=("theme_id", "nunique"),
        mean_latest_mosaic_z=("latest_mosaic_z_score", "mean"),
        mean_apwc_rolling_z=("apwc_rolling_z", "mean"),
        mean_future_residual=("future_residual_return", "mean"),
        mean_future_total=("future_total_return", "mean"),
    ).reset_index()
    return out



print("Building weekly signal panel...")
weekly_signal_panel = build_weekly_coherence_momentum_panel(weekly_cfg)
print("Running weekly rolling-Z baseline strategy diagnostics...")
weekly_strategy_panel, weekly_selected_themes = build_weekly_strategy_returns(weekly_signal_panel, weekly_cfg)
weekly_strategy_summary = summarize_weekly_strategy(weekly_strategy_panel, weekly_cfg)
print("Running weekly rolling-Z baseline statistical diagnostics...")
weekly_factor_decomposition_table = run_factor_decomposition(weekly_strategy_panel) if not weekly_strategy_panel.empty else pd.DataFrame()
print("  weekly IC...")
weekly_ic_summary = weekly_ic_table(weekly_signal_panel)
print("  weekly predictive regressions...")
weekly_regression_summary = weekly_predictive_regressions(weekly_signal_panel)
print("  weekly threshold/top-N sweep...")
weekly_sweep_summary = weekly_threshold_sweep(weekly_signal_panel, weekly_cfg)
print("  weekly gate diagnostics...")
weekly_gate_diagnostic_table = weekly_gate_diagnostics(weekly_signal_panel)

# Weekly rolling-Z + RRG validation suite.
print("Building weekly rolling-Z RRG validation suite...")
weekly_rrg_panels = build_weekly_rrg_suite(weekly_signal_panel, weekly_cfg, rrg_cfg)
weekly_rrg_default_key = "residual__zero__time_series"
weekly_rrg_default_panel = weekly_rrg_panels.get(weekly_rrg_default_key, next(iter(weekly_rrg_panels.values()), pd.DataFrame()))
weekly_rrg_summary = pd.concat(
    [summarize_weekly_rrg_panel(panel, key) for key, panel in weekly_rrg_panels.items()],
    ignore_index=True,
) if weekly_rrg_panels else pd.DataFrame()
print("Summarizing weekly rolling-Z RRG panels...")
weekly_rrg_quadrant_forward_table = weekly_rrg_quadrant_forward_return_table(weekly_rrg_panels)
weekly_rrg_transition_forward_table = weekly_rrg_transition_forward_return_table(weekly_rrg_panels)
weekly_rrg_ic_panel_keys = [k for k in [weekly_rrg_default_key, "total__zero__time_series"] if k in weekly_rrg_panels]
weekly_rrg_ic_panels = {k: weekly_rrg_panels[k] for k in weekly_rrg_ic_panel_keys}
weekly_rrg_ic_summary = weekly_rrg_ic_table(weekly_rrg_ic_panels)
weekly_rrg_predictive_regression_summary = weekly_rrg_predictive_regressions(weekly_rrg_default_panel, weekly_cfg) if not weekly_rrg_default_panel.empty else pd.DataFrame()
print("Building weekly rolling-Z RRG portfolio diagnostics...")
weekly_rrg_strategy_panel, weekly_rrg_selected_themes = build_weekly_rrg_portfolio_returns(weekly_rrg_default_panel, weekly_cfg) if not weekly_rrg_default_panel.empty else (pd.DataFrame(), pd.DataFrame())
weekly_rrg_strategy_summary = summarize_weekly_rrg_portfolio(weekly_rrg_strategy_panel)
print("Running weekly rolling-Z RRG threshold/top-N sweep...")
weekly_rrg_sweep_summary = weekly_rrg_threshold_topn_sweep(weekly_rrg_panels, weekly_cfg)
print("Running weekly rolling-Z RRG turnover/cost stress...")
weekly_rrg_cost_stress_table = weekly_rrg_turnover_cost_stress(weekly_rrg_default_panel, weekly_cfg) if not weekly_rrg_default_panel.empty else pd.DataFrame()
print("Running weekly rolling-Z RRG placebo test...")
weekly_rrg_placebo_table = weekly_rrg_placebo_gate_test(weekly_rrg_default_panel, weekly_cfg) if not weekly_rrg_default_panel.empty else pd.DataFrame()
print("Running weekly rolling-Z RRG walk-forward validation...")
weekly_rrg_walk_forward_table = weekly_rrg_walk_forward_validation(weekly_rrg_default_panel, weekly_cfg) if not weekly_rrg_default_panel.empty else pd.DataFrame()
print("Checking Mosaic z-score / weekly rolling-Z overlap...")
weekly_rrg_mosaic_overlap_table = weekly_rrg_mosaic_gate_overlap(weekly_rrg_default_panel, analysis_results, cfg.z_threshold, weekly_cfg.apwc_z_threshold) if not weekly_rrg_default_panel.empty else pd.DataFrame()

weekly_strategy_timing_ok = bool(
    not weekly_signal_panel.empty
    and (weekly_signal_panel["past_end"] <= weekly_signal_panel["analysis_date"]).all()
    and (weekly_signal_panel["future_start"] > weekly_signal_panel["analysis_date"]).all()
)
assert weekly_strategy_timing_ok
if not weekly_signal_panel.empty:
    assert weekly_signal_panel["apwc_rolling_z"].notna().any(), "APWC rolling-Z score was not computed."

weekly_rrg_timing_ok = bool(
    not weekly_rrg_default_panel.empty
    and (weekly_rrg_default_panel["past_end"] <= weekly_rrg_default_panel["analysis_date"]).all()
    and (weekly_rrg_default_panel["future_start"] > weekly_rrg_default_panel["analysis_date"]).all()
)
assert weekly_rrg_timing_ok or weekly_rrg_default_panel.empty
if not weekly_rrg_default_panel.empty:
    assert weekly_rrg_default_panel["weekly_pattern_b_score_soft_gate"].notna().any(), "Weekly rolling-Z RRG scores were not computed."

weekly_strategy_research_plan = pd.DataFrame(
    [
        {
            "analysis": "Incremental predictive regression",
            "purpose": "APWC rolling-Zが単純なtotal/residual momentumに対して追加説明力を持つかを確認する。",
            "implemented_table": "weekly_regression_summary",
        },
        {
            "analysis": "Threshold / top-N sweep",
            "purpose": "閾値0に依存した結果でないか、投資率・収益率・Sharpeのトレードオフを確認する。",
            "implemented_table": "weekly_sweep_summary",
        },
        {
            "analysis": "Cross-sectional IC",
            "purpose": "各週のテーマ横断ランキング情報が将来total/residual returnに効いているかを確認する。",
            "implemented_table": "weekly_ic_summary",
        },
        {
            "analysis": "Residual-vs-total decomposition",
            "purpose": "収益が既存ファクターではなくテーマ固有残差から来ているかを確認する。",
            "implemented_table": "weekly_factor_decomposition_table",
        },
        {
            "analysis": "Weekly rolling-Z RRG panel suite",
            "purpose": "rolling-Z gateをcoherence regime、RRGを方向・順位付けとして使う全variantを計算する。",
            "implemented_table": "weekly_rrg_panels / weekly_rrg_summary",
        },
        {
            "analysis": "RRG quadrant forward returns",
            "purpose": "Leading / Improving / Weakening / Laggingの将来リターン順序性を確認する。",
            "implemented_table": "weekly_rrg_quadrant_forward_table",
        },
        {
            "analysis": "RRG transition forward returns",
            "purpose": "Improving→Leadingがentry、Weakening→Laggingがexit/shortとして有効かを確認する。",
            "implemented_table": "weekly_rrg_transition_forward_table",
        },
        {
            "analysis": "RRG incremental regression and IC",
            "purpose": "rolling-Z、RS-Ratio、RS-Momentum、soft-gated scoreの追加説明力と横断ランキング能力を検証する。",
            "implemented_table": "weekly_rrg_predictive_regression_summary / weekly_rrg_ic_summary",
        },
        {
            "analysis": "RRG threshold / top-N sweep",
            "purpose": "rolling-Z閾値、採用テーマ数、RRG方式への感応度を確認する。",
            "implemented_table": "weekly_rrg_sweep_summary",
        },
        {
            "analysis": "Placebo rolling-Z gate",
            "purpose": "同一週内でrolling-Zをテーマ間シャッフルし、gateが偶然でないかを確認する。",
            "implemented_table": "weekly_rrg_placebo_table",
        },
        {
            "analysis": "Turnover / transaction-cost stress",
            "purpose": "週次RRG戦略の入替負荷とコスト後期待値を確認する。",
            "implemented_table": "weekly_rrg_cost_stress_table",
        },
        {
            "analysis": "Walk-forward validation",
            "purpose": "訓練期間と将来期間に分割し、固定weekly RRG ruleが将来側で崩れないか確認する。",
            "implemented_table": "weekly_rrg_walk_forward_table",
        },
        {
            "analysis": "Mosaic z-score conservative overlay",
            "purpose": "利用可能な最新Mosaic z-scoreとweekly rolling-Z gateの重なりを確認する。",
            "implemented_table": "weekly_rrg_mosaic_overlap_table",
        },
    ]
)

print("Weekly APWC rolling-Z reference config")
display(pd.Series(weekly_cfg.__dict__))
print("Weekly strategy summary")
display(weekly_strategy_summary)
print("Weekly IC summary")
display(weekly_ic_summary)
print("Weekly predictive regressions")
display(weekly_regression_summary)
print("Weekly threshold / top-N sweep")
display(weekly_sweep_summary.head(20))
print("Weekly factor decomposition")
display(weekly_factor_decomposition_table)
print("Weekly gate diagnostics tail")
display(weekly_gate_diagnostic_table.tail())
print("Weekly rolling-Z RRG default panel sample")
if not weekly_rrg_default_panel.empty:
    display(weekly_rrg_default_panel[[
        "theme_id", "analysis_date", "apwc_rolling_z", "rolling_z_coherence_state",
        "rs_ratio", "rs_momentum", "rrg_quadrant", "rrg_transition",
        "weekly_pattern_b_score_soft_gate", "weekly_two_layer_score",
        "future_residual_return", "future_total_return"
    ]].tail(20))
else:
    display(pd.DataFrame())
print("Weekly rolling-Z RRG summary")
display(weekly_rrg_summary.head(30))
print("Weekly RRG quadrant forward-return diagnostics")
display(weekly_rrg_quadrant_forward_table.head(40))
print("Weekly RRG transition forward-return diagnostics")
display(weekly_rrg_transition_forward_table.head(40))
print("Weekly RRG predictive regressions")
display(weekly_rrg_predictive_regression_summary)
print("Weekly RRG IC summary")
display(weekly_rrg_ic_summary.head(40))
print("Weekly RRG strategy summary")
display(weekly_rrg_strategy_summary)
print("Weekly RRG threshold / top-N sweep")
display(weekly_rrg_sweep_summary.head(40))
print("Weekly RRG turnover and transaction-cost stress")
display(weekly_rrg_cost_stress_table)
print("Weekly RRG placebo rolling-Z gate test")
display(weekly_rrg_placebo_table)
print("Weekly RRG walk-forward validation")
display(weekly_rrg_walk_forward_table)
print("Weekly Mosaic z-score / rolling-Z gate overlap")
display(weekly_rrg_mosaic_overlap_table)
print("Weekly strategy research plan")
display(weekly_strategy_research_plan)


# ## 11. 検証サマリー

# In[14]:


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
    "rrg_suite_available": bool(len(rrg_panels) > 0),
    "rrg_suite_panel_count": int(len(rrg_panels)),
    "rrg_default_panel": rrg_default_key,
    "weekly_reference_strategy_available": bool(not weekly_strategy_panel.empty),
    "weekly_rebalance_count": int(weekly_strategy_panel["analysis_date"].nunique()) if not weekly_strategy_panel.empty else 0,
    "weekly_strategy_timing_ok": bool(weekly_strategy_timing_ok),
    "weekly_rrg_suite_available": bool(len(weekly_rrg_panels) > 0),
    "weekly_rrg_panel_count": int(len(weekly_rrg_panels)),
    "weekly_rrg_default_panel": weekly_rrg_default_key,
    "weekly_rrg_timing_ok": bool(weekly_rrg_timing_ok),
    "weekly_rrg_strategy_available": bool(not weekly_rrg_strategy_panel.empty),
    "weekly_rrg_placebo_reps": int(weekly_cfg.rrg_placebo_reps),
    "weekly_rrg_walk_forward_available": bool(not weekly_rrg_walk_forward_table.empty),
    "weekly_research_plan_rows": int(len(weekly_strategy_research_plan)),
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
print("rrg_summary")
display(rrg_summary)
print("weekly_strategy_summary")
display(weekly_strategy_summary)
print("weekly_rrg_strategy_summary")
display(weekly_rrg_strategy_summary)
print("weekly_rrg_placebo_table")
display(weekly_rrg_placebo_table)
print("weekly_rrg_walk_forward_table")
display(weekly_rrg_walk_forward_table)
print("weekly_research_plan")
display(weekly_strategy_research_plan)
