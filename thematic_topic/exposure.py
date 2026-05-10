"""topic × theme exposure 構築。"""

from __future__ import annotations

import pandas as pd



def build_exposure(
    topic_intensity_df: pd.DataFrame,
    topic_theme_map_df: pd.DataFrame,
    intensity_col: str = "topic_ewma",
) -> pd.DataFrame:
    required_intensity = {"date", "topic_id", intensity_col}
    required_map = {"topic_id", "theme_id", "topic_theme_similarity"}

    missing_i = sorted(required_intensity - set(topic_intensity_df.columns))
    missing_m = sorted(required_map - set(topic_theme_map_df.columns))
    if missing_i:
        raise ValueError(f"topic_intensity 必須カラム不足: {missing_i}")
    if missing_m:
        raise ValueError(f"topic_theme_map 必須カラム不足: {missing_m}")

    merged = topic_intensity_df.merge(topic_theme_map_df, on="topic_id", how="inner")
    merged["topic_intensity"] = merged[intensity_col].astype(float)
    merged["theme_topic_exposure"] = merged["topic_intensity"] * merged["topic_theme_similarity"].astype(float)

    out = merged[
        [
            "date",
            "theme_id",
            "topic_id",
            "theme_topic_exposure",
            "topic_intensity",
            "topic_theme_similarity",
        ]
    ].copy()
    out = out.sort_values(["date", "theme_id", "topic_id"]).reset_index(drop=True)
    return out
