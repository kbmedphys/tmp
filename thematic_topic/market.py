"""市場反応ターゲット生成。"""

from __future__ import annotations

import numpy as np
import pandas as pd



def _forward_cum_return(values: np.ndarray, horizon: int) -> np.ndarray:
    out = np.full(len(values), np.nan, dtype=float)
    for i in range(len(values)):
        end = i + horizon
        if end >= len(values):
            continue
        window = values[i + 1 : end + 1]
        if np.isnan(window).any():
            continue
        out[i] = float(np.prod(1.0 + window) - 1.0)
    return out



def build_theme_market_series(
    theme_holdings_df: pd.DataFrame,
    prices_df: pd.DataFrame,
) -> pd.DataFrame:
    required_holdings = {"date", "theme_id", "ticker", "weight"}
    required_prices = {"date", "ticker", "close"}

    missing_h = sorted(required_holdings - set(theme_holdings_df.columns))
    missing_p = sorted(required_prices - set(prices_df.columns))
    if missing_h:
        raise ValueError(f"theme_holdings 必須カラム不足: {missing_h}")
    if missing_p:
        raise ValueError(f"prices 必須カラム不足: {missing_p}")

    px = prices_df.copy()
    px["date"] = pd.to_datetime(px["date"], errors="coerce").dt.normalize()
    px = px.dropna(subset=["date"]).sort_values(["ticker", "date"])
    px["stock_return"] = px.groupby("ticker")["close"].pct_change()

    if "turnover" not in px.columns:
        raise ValueError("prices に turnover カラムが必要です（attentionモデル用）。")

    px["turnover"] = pd.to_numeric(px["turnover"], errors="coerce")

    holdings = theme_holdings_df.copy()
    holdings["date"] = pd.to_datetime(holdings["date"], errors="coerce").dt.normalize()
    holdings = holdings.dropna(subset=["date"]).sort_values(["theme_id", "ticker", "date"])

    merged_rows: list[pd.DataFrame] = []
    for (theme_id, ticker), h in holdings.groupby(["theme_id", "ticker"]):
        p = px[px["ticker"] == ticker][["date", "ticker", "stock_return", "turnover"]]
        if p.empty:
            continue
        h_sorted = h[["date", "weight"]].sort_values("date")
        m = pd.merge_asof(p.sort_values("date"), h_sorted, on="date", direction="backward")
        m["theme_id"] = str(theme_id)
        merged_rows.append(m)

    if not merged_rows:
        return pd.DataFrame(columns=["date", "theme_id", "theme_return", "theme_turnover"])

    merged = pd.concat(merged_rows, ignore_index=True)
    merged["weight"] = pd.to_numeric(merged["weight"], errors="coerce").fillna(0.0)

    denom = merged.groupby(["date", "theme_id"])["weight"].transform("sum").replace(0.0, np.nan)
    merged["w_norm"] = merged["weight"] / denom

    merged["ret_contrib"] = merged["w_norm"] * merged["stock_return"].fillna(0.0)
    merged["turn_contrib"] = merged["w_norm"] * merged["turnover"].fillna(0.0)

    out = (
        merged.groupby(["date", "theme_id"], as_index=False)
        .agg(theme_return=("ret_contrib", "sum"), theme_turnover=("turn_contrib", "sum"))
        .sort_values(["theme_id", "date"])
        .reset_index(drop=True)
    )
    return out



def build_market_targets(
    theme_market_df: pd.DataFrame,
    market_turnover_df: pd.DataFrame | None = None,
    horizon: int = 5,
    turnover_ma_window: int = 20,
) -> pd.DataFrame:
    required = {"date", "theme_id", "theme_return", "theme_turnover"}
    missing = sorted(required - set(theme_market_df.columns))
    if missing:
        raise ValueError(f"theme_market_df 必須カラム不足: {missing}")

    df = theme_market_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    df = df.dropna(subset=["date"]).sort_values(["theme_id", "date"]).reset_index(drop=True)

    if market_turnover_df is None or market_turnover_df.empty:
        market_turnover = (
            df.groupby("date", as_index=False)["theme_turnover"].sum().rename(columns={"theme_turnover": "market_turnover"})
        )
    else:
        market_turnover = market_turnover_df.copy()
        market_turnover["date"] = pd.to_datetime(market_turnover["date"], errors="coerce").dt.normalize()

    df = df.merge(market_turnover[["date", "market_turnover"]], on="date", how="left")
    df["rel_turnover"] = df["theme_turnover"] / df["market_turnover"].replace(0.0, np.nan)

    df["abnormal_turnover_raw"] = (
        df.groupby("theme_id")["rel_turnover"].transform(lambda s: s - s.rolling(turnover_ma_window, min_periods=5).mean().shift(1))
    )

    mu = df.groupby("theme_id")["abnormal_turnover_raw"].transform("mean")
    sd = df.groupby("theme_id")["abnormal_turnover_raw"].transform("std").replace(0.0, np.nan)
    df["abnormal_turnover_z"] = (df["abnormal_turnover_raw"] - mu) / sd

    df["forward_return"] = (
        df.groupby("theme_id")["theme_return"].transform(lambda s: _forward_cum_return(s.to_numpy(dtype=float), horizon))
    )

    df["y_attention"] = df["abnormal_turnover_z"]
    df["y_return"] = df["forward_return"]

    out_cols = [
        "date",
        "theme_id",
        "theme_return",
        "theme_turnover",
        "market_turnover",
        "rel_turnover",
        "abnormal_turnover_raw",
        "abnormal_turnover_z",
        "forward_return",
        "y_attention",
        "y_return",
    ]
    return df[out_cols]
