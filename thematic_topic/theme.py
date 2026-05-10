"""テーマ定義処理と topic-theme 対応。"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


THEME_PROFILE_COLUMNS = [
    "theme_name",
    "theme_description",
    "positive_drivers",
    "negative_drivers",
    "related_keywords",
    "excluded_keywords",
    "constituent_names",
    "constituent_descriptions",
    "gics_industries",
    "trbc_industries",
]



def build_theme_profiles(theme_df: pd.DataFrame) -> pd.DataFrame:
    required = ["theme_id"] + THEME_PROFILE_COLUMNS
    missing = sorted(set(required) - set(theme_df.columns))
    if missing:
        raise ValueError(f"theme profile 必須カラム不足: {missing}")

    out = theme_df.copy()
    for col in THEME_PROFILE_COLUMNS:
        out[col] = out[col].fillna("").astype(str)

    out["theme_profile_text"] = out.apply(
        lambda r: "\n".join(
            [
                f"theme_name: {r['theme_name']}",
                f"theme_description: {r['theme_description']}",
                f"positive_drivers: {r['positive_drivers']}",
                f"negative_drivers: {r['negative_drivers']}",
                f"related_keywords: {r['related_keywords']}",
                f"excluded_keywords: {r['excluded_keywords']}",
                f"constituent_names: {r['constituent_names']}",
                f"constituent_descriptions: {r['constituent_descriptions']}",
                f"gics_industries: {r['gics_industries']}",
                f"trbc_industries: {r['trbc_industries']}",
            ]
        ),
        axis=1,
    )
    return out



def map_topics_to_themes(
    topic_summary_df: pd.DataFrame,
    theme_profile_df: pd.DataFrame,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    similarity_threshold: float = 0.35,
    top_n_themes_per_topic: int = 5,
) -> pd.DataFrame:
    required_topic = ["topic_id", "topic_summary_text"]
    required_theme = ["theme_id", "theme_profile_text"]

    missing_topic = sorted(set(required_topic) - set(topic_summary_df.columns))
    missing_theme = sorted(set(required_theme) - set(theme_profile_df.columns))
    if missing_topic:
        raise ValueError(f"topic_summary 必須カラム不足: {missing_topic}")
    if missing_theme:
        raise ValueError(f"theme_profile 必須カラム不足: {missing_theme}")

    topics = topic_summary_df.copy()
    themes = theme_profile_df.copy()

    model = SentenceTransformer(model_name)
    topic_emb = model.encode(topics["topic_summary_text"].fillna("").astype(str).tolist(), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    theme_emb = model.encode(themes["theme_profile_text"].fillna("").astype(str).tolist(), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)

    score = np.matmul(topic_emb, theme_emb.T)

    rows: list[dict[str, object]] = []
    for i, topic_row in topics.reset_index(drop=True).iterrows():
        sims = score[i]
        ranking = np.argsort(-sims)
        for rank, j in enumerate(ranking, start=1):
            rows.append(
                {
                    "topic_id": int(topic_row["topic_id"]),
                    "theme_id": str(themes.iloc[j]["theme_id"]),
                    "topic_theme_similarity": float(sims[j]),
                    "rank_in_topic": int(rank),
                }
            )

    out = pd.DataFrame(rows)
    out = out[(out["topic_theme_similarity"] >= similarity_threshold) & (out["rank_in_topic"] <= top_n_themes_per_topic)].copy()
    out = out.sort_values(["topic_id", "rank_in_topic"]).reset_index(drop=True)
    return out
