"""トピック強度時系列。"""

from __future__ import annotations

import numpy as np
import pandas as pd



def _calc_persistence(z: pd.Series, threshold: float) -> pd.Series:
    counter = 0
    out: list[int] = []
    for value in z.fillna(-np.inf).tolist():
        if value > threshold:
            counter += 1
        else:
            counter = 0
        out.append(counter)
    return pd.Series(out, index=z.index, dtype=float)



def _add_metrics(df: pd.DataFrame, ewma_span: int, lookback: int, z_threshold: float) -> pd.DataFrame:
    out = df.copy().sort_values("date").reset_index(drop=True)

    out["topic_ewma"] = out["topic_prob_sum"].ewm(span=ewma_span, adjust=False).mean()
    ma = out["topic_prob_sum"].rolling(lookback, min_periods=5).mean().shift(1)
    sd = out["topic_prob_sum"].rolling(lookback, min_periods=5).std(ddof=0).shift(1)
    out["topic_z"] = (out["topic_prob_sum"] - ma) / sd.replace(0.0, np.nan)

    out["topic_delta"] = out["topic_prob_sum"].diff()
    out["topic_accel"] = out["topic_delta"].diff()
    out["topic_persistence"] = _calc_persistence(out["topic_z"], z_threshold)

    return out



def _aggregate_for_freq(base: pd.DataFrame, freq: str) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for topic_id, group in base.groupby("topic_id"):
        tmp = group[["period_ts", "topic_probability"]].copy()
        tmp = tmp.set_index("period_ts")
        agg = pd.DataFrame()
        agg["topic_count"] = tmp["topic_probability"].resample(freq).size()
        agg["topic_prob_sum"] = tmp["topic_probability"].resample(freq).sum(min_count=1)
        agg["topic_prob_mean"] = tmp["topic_probability"].resample(freq).mean()
        agg = agg.reset_index().rename(columns={"period_ts": "date"})
        agg["topic_id"] = int(topic_id)
        rows.append(agg)

    if not rows:
        return pd.DataFrame(columns=["date", "topic_id", "topic_count", "topic_prob_sum", "topic_prob_mean"])

    out = pd.concat(rows, ignore_index=True)
    out["topic_count"] = out["topic_count"].fillna(0).astype(int)
    out["topic_prob_sum"] = out["topic_prob_sum"].fillna(0.0)
    out["topic_prob_mean"] = out["topic_prob_mean"].fillna(0.0)
    return out



def build_topic_intensity(
    topic_assignments: pd.DataFrame,
    weekly_rule: str = "W-FRI",
    ewma_span: int = 5,
    lookback: int = 20,
    z_threshold: float = 1.0,
    aggregate_timezone: str = "Asia/Tokyo",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """daily/weekly の topic 強度を生成する。"""
    required = {"timestamp", "topic_id", "topic_probability"}
    missing = sorted(required - set(topic_assignments.columns))
    if missing:
        raise ValueError(f"build_topic_intensity 入力カラム不足: {missing}")

    base = topic_assignments.copy()
    base["timestamp"] = pd.to_datetime(base["timestamp"], utc=True, errors="coerce")
    base = base.dropna(subset=["timestamp"]).copy()

    outlier_stats = pd.DataFrame(
        [
            {
                "n_docs": int(len(base)),
                "n_outliers": int((base["topic_id"] == -1).sum()),
                "outlier_ratio": float((base["topic_id"] == -1).mean()) if len(base) > 0 else np.nan,
            }
        ]
    )

    valid = base[base["topic_id"] != -1].copy()
    if valid.empty:
        empty_cols = [
            "date",
            "topic_id",
            "topic_count",
            "topic_prob_sum",
            "topic_prob_mean",
            "topic_ewma",
            "topic_z",
            "topic_delta",
            "topic_accel",
            "topic_persistence",
        ]
        return pd.DataFrame(columns=empty_cols), pd.DataFrame(columns=empty_cols), outlier_stats

    local_ts = valid["timestamp"].dt.tz_convert(aggregate_timezone)
    valid["period_ts"] = local_ts

    daily = _aggregate_for_freq(valid, "D")
    weekly = _aggregate_for_freq(valid, weekly_rule)

    daily = pd.concat(
        [_add_metrics(g, ewma_span, lookback, z_threshold) for _, g in daily.groupby("topic_id")], ignore_index=True
    )
    weekly = pd.concat(
        [_add_metrics(g, ewma_span, lookback, z_threshold) for _, g in weekly.groupby("topic_id")], ignore_index=True
    )

    return daily, weekly, outlier_stats
