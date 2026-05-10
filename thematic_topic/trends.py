"""Trend, Alert, Ranking, Explanation 生成。"""

from __future__ import annotations

import numpy as np
import pandas as pd



def _persistence(series: pd.Series, threshold: float = 1.0) -> pd.Series:
    run = 0
    out: list[int] = []
    for v in series.fillna(-np.inf).tolist():
        if v > threshold:
            run += 1
        else:
            run = 0
        out.append(run)
    return pd.Series(out, index=series.index, dtype=float)



def _with_trend_metrics(df: pd.DataFrame, ewma_span: int, lookback: int) -> pd.DataFrame:
    out = df.copy().sort_values("date")
    out["trend_ewma"] = out["trend_value"].ewm(span=ewma_span, adjust=False).mean()

    ma = out["trend_ewma"].rolling(lookback, min_periods=10).mean().shift(1)
    sd = out["trend_ewma"].rolling(lookback, min_periods=10).std(ddof=0).shift(1)
    out["trend_z"] = (out["trend_ewma"] - ma) / sd.replace(0.0, np.nan)

    out["trend_5d_change"] = out["trend_ewma"].diff(5)
    out["trend_20d_change"] = out["trend_ewma"].diff(20)
    out["trend_persistence"] = _persistence(out["trend_z"], threshold=1.0)
    return out



def _zscore_cross_section(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or np.isnan(std):
        return pd.Series(np.zeros(len(series)), index=series.index, dtype=float)
    return (series - series.mean()) / std



def build_trends_alerts_rankings(
    exposure_df: pd.DataFrame,
    beta_df: pd.DataFrame,
    topic_summary_df: pd.DataFrame,
    topic_theme_map_df: pd.DataFrame,
    theme_profile_df: pd.DataFrame,
    trend_ewma_span: int = 5,
    trend_lookback: int = 60,
    surge_threshold: float = 2.0,
    uptrend_threshold: float = 1.0,
    persistent_threshold: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """trend/alert/ranking/explanation テーブルを作成する。"""
    required_exposure = {"date", "theme_id", "topic_id", "theme_topic_exposure"}
    required_beta = {"theme_id", "topic_id", "target", "beta", "fitted"}

    miss_e = sorted(required_exposure - set(exposure_df.columns))
    miss_b = sorted(required_beta - set(beta_df.columns))
    if miss_e:
        raise ValueError(f"exposure 必須カラム不足: {miss_e}")
    if miss_b:
        raise ValueError(f"beta 必須カラム不足: {miss_b}")

    exp = exposure_df.copy()
    exp["date"] = pd.to_datetime(exp["date"], errors="coerce")
    exp["topic_id_str"] = exp["topic_id"].astype(str)

    bet = beta_df.copy()
    bet = bet[(bet["fitted"] == True) & (bet["topic_id"] != "__SKIPPED__")].copy()  # noqa: E712
    bet["topic_id_str"] = bet["topic_id"].astype(str)

    contrib = exp.merge(
        bet[["theme_id", "topic_id_str", "target", "beta"]],
        on=["theme_id", "topic_id_str"],
        how="inner",
    )
    contrib["contribution"] = contrib["theme_topic_exposure"] * contrib["beta"]

    active_topics = (
        exp.groupby(["date", "theme_id"], as_index=False)
        .agg(active_topics=("topic_id", "nunique"))
    )

    trend_rows: list[pd.DataFrame] = []
    for (theme_id, target), g in contrib.groupby(["theme_id", "target"]):
        t = g.groupby("date", as_index=False)["contribution"].sum().rename(columns={"contribution": "trend_value"})
        t["theme_id"] = str(theme_id)
        t["target"] = str(target)
        trend_rows.append(t)

    if not trend_rows:
        empty = pd.DataFrame()
        return empty, empty, empty, empty

    trend_df = pd.concat(trend_rows, ignore_index=True)
    trend_df = trend_df.merge(active_topics, on=["date", "theme_id"], how="left")

    trend_df = pd.concat(
        [
            _with_trend_metrics(g, trend_ewma_span, trend_lookback)
            for (_, _), g in trend_df.groupby(["theme_id", "target"])
        ],
        ignore_index=True,
    )

    trend_df["alert_surge"] = trend_df["trend_z"] >= surge_threshold
    trend_df["alert_uptrend"] = (trend_df["trend_z"] >= uptrend_threshold) & (trend_df["trend_5d_change"] > 0)
    trend_df["alert_persistent"] = trend_df["trend_persistence"] >= persistent_threshold
    trend_df["alert_level"] = (
        trend_df["alert_surge"].astype(int)
        + trend_df["alert_uptrend"].astype(int)
        + trend_df["alert_persistent"].astype(int)
    )

    alert_df = trend_df[
        [
            "date",
            "theme_id",
            "target",
            "trend_z",
            "trend_5d_change",
            "trend_persistence",
            "alert_uptrend",
            "alert_surge",
            "alert_persistent",
            "alert_level",
        ]
    ].copy()

    theme_names = theme_profile_df[["theme_id", "theme_name"]].drop_duplicates() if "theme_name" in theme_profile_df.columns else pd.DataFrame(columns=["theme_id", "theme_name"])
    trend_named = trend_df.merge(theme_names, on="theme_id", how="left")

    latest_date = trend_named["date"].max()
    latest = trend_named[trend_named["date"] == latest_date].copy()

    ranking_parts: list[pd.DataFrame] = []
    for target in ["attention", "return"]:
        part = latest[latest["target"] == target].sort_values("trend_z", ascending=False).copy()
        part["rank"] = np.arange(1, len(part) + 1)
        part["ranking_type"] = target
        ranking_parts.append(part)

    attention_latest = latest[latest["target"] == "attention"]
    return_latest = latest[latest["target"] == "return"]

    mega = attention_latest[["date", "theme_id", "theme_name", "trend_z", "trend_persistence", "active_topics"]].rename(
        columns={"trend_z": "attention_trend_z", "trend_persistence": "attention_persistence"}
    )
    if not return_latest.empty:
        mega = mega.merge(
            return_latest[["theme_id", "trend_z"]].rename(columns={"trend_z": "return_trend_z"}),
            on="theme_id",
            how="left",
        )
        mega["return_trend_z"] = mega["return_trend_z"].fillna(0.0)
        mega["mega_trend_score"] = (
            0.5 * mega["attention_trend_z"].fillna(0.0)
            + 0.2 * mega["return_trend_z"]
            + 0.2 * _zscore_cross_section(mega["attention_persistence"].fillna(0.0))
            + 0.1 * _zscore_cross_section(mega["active_topics"].fillna(0.0))
        )
    else:
        mega["return_trend_z"] = 0.0
        mega["mega_trend_score"] = (
            0.6 * mega["attention_trend_z"].fillna(0.0)
            + 0.3 * _zscore_cross_section(mega["attention_persistence"].fillna(0.0))
            + 0.1 * _zscore_cross_section(mega["active_topics"].fillna(0.0))
        )

    mega = mega.sort_values("mega_trend_score", ascending=False).copy()
    mega["rank"] = np.arange(1, len(mega) + 1)
    mega["ranking_type"] = "mega"
    mega = mega.merge(
        attention_latest[["theme_id", "trend_value", "trend_ewma", "trend_5d_change", "trend_20d_change", "trend_persistence"]],
        on="theme_id",
        how="left",
    )
    mega["trend_z"] = mega["mega_trend_score"]

    ranking_parts.append(mega)

    ranking_df = pd.concat(ranking_parts, ignore_index=True, sort=False)
    ranking_df = ranking_df[
        [
            "ranking_type",
            "rank",
            "date",
            "theme_id",
            "theme_name",
            "trend_value",
            "trend_ewma",
            "trend_z",
            "trend_5d_change",
            "trend_20d_change",
            "trend_persistence",
            "active_topics",
        ]
    ].sort_values(["ranking_type", "rank"]).reset_index(drop=True)

    topic_meta = topic_summary_df[["topic_id", "top_words", "representative_headlines"]].copy()
    topic_meta["topic_id_str"] = topic_meta["topic_id"].astype(str)

    exposure_latest = exp[exp["date"] == latest_date].copy()
    explanation = exposure_latest.merge(
        topic_theme_map_df[["topic_id", "theme_id", "topic_theme_similarity"]],
        on=["topic_id", "theme_id"],
        how="left",
    )
    explanation["topic_id_str"] = explanation["topic_id"].astype(str)

    beta_attn = bet[bet["target"] == "attention"][["theme_id", "topic_id_str", "beta"]].rename(columns={"beta": "beta_attention"})
    beta_ret = bet[bet["target"] == "return"][["theme_id", "topic_id_str", "beta"]].rename(columns={"beta": "beta_return"})

    explanation = explanation.merge(beta_attn, on=["theme_id", "topic_id_str"], how="left")
    explanation = explanation.merge(beta_ret, on=["theme_id", "topic_id_str"], how="left")
    explanation = explanation.merge(topic_meta[["topic_id_str", "top_words", "representative_headlines"]], on="topic_id_str", how="left")
    explanation = explanation.merge(theme_names, on="theme_id", how="left")

    explanation = explanation[
        [
            "theme_id",
            "theme_name",
            "topic_id",
            "topic_theme_similarity",
            "top_words",
            "theme_topic_exposure",
            "beta_attention",
            "beta_return",
            "representative_headlines",
        ]
    ].rename(columns={"top_words": "topic_keywords"})

    explanation = explanation.sort_values(["theme_id", "theme_topic_exposure"], ascending=[True, False]).reset_index(drop=True)

    return trend_df, alert_df, ranking_df, explanation
