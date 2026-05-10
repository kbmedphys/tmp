"""BERTopic による潜在トピック抽出。"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

from .config import TopicModelSettings



def _build_tokenizer(stopwords: set[str]) -> Callable[[str], list[str]]:
    from janome.tokenizer import Tokenizer

    tokenizer = Tokenizer()
    allowed_pos = {"名詞", "動詞", "形容詞"}

    def tokenize(text: str) -> list[str]:
        out: list[str] = []
        for token in tokenizer.tokenize(text):
            base = token.base_form
            if base == "*":
                base = token.surface
            base = str(base).strip()
            if not base:
                continue
            major_pos = token.part_of_speech.split(",")[0]
            if major_pos not in allowed_pos:
                continue
            if base in stopwords:
                continue
            out.append(base)
        return out

    return tokenize



def build_japanese_vectorizer(stopwords: list[str]) -> CountVectorizer:
    return CountVectorizer(
        tokenizer=_build_tokenizer(set(stopwords)),
        token_pattern=None,
        lowercase=False,
        min_df=2,
    )



def _build_topic_model(settings: TopicModelSettings):
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from umap import UMAP

    umap_model = UMAP(
        n_neighbors=settings.umap_n_neighbors,
        n_components=settings.umap_n_components,
        min_dist=settings.umap_min_dist,
        metric=settings.umap_metric,
        random_state=settings.random_state,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=settings.hdbscan_min_cluster_size,
        metric=settings.hdbscan_metric,
        cluster_selection_method=settings.hdbscan_cluster_selection_method,
        prediction_data=True,
    )

    vectorizer_model = build_japanese_vectorizer(settings.tokenizer_stopwords)

    model = BERTopic(
        embedding_model=None,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        top_n_words=settings.top_n_words,
        calculate_probabilities=settings.calculate_probabilities,
        language=settings.language,
        verbose=False,
    )
    return model



def _build_assignments(df: pd.DataFrame, topics: list[int] | np.ndarray, probs: np.ndarray | None) -> pd.DataFrame:
    assignments = df[["news_id", "timestamp", "headline_clean"]].copy().reset_index(drop=True)
    assignments["topic_id"] = [int(t) for t in topics]

    if probs is None:
        assignments["topic_probability"] = np.nan
    else:
        prob_array = np.asarray(probs)
        if prob_array.ndim == 1:
            assignments["topic_probability"] = prob_array.astype(float)
        else:
            assignments["topic_probability"] = prob_array.max(axis=1).astype(float)

    return assignments



def _build_topic_summary(
    assignments: pd.DataFrame,
    topic_model,
    top_n_headlines: int,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    topic_ids = sorted({int(x) for x in assignments["topic_id"].dropna().tolist()})
    for topic_id in topic_ids:
        group = assignments[assignments["topic_id"] == topic_id]
        topic_words = [] if topic_id == -1 else (topic_model.get_topic(topic_id) or [])
        top_words = [w for w, _ in topic_words]
        top_scores = [float(s) for _, s in topic_words]

        reps = (
            group.sort_values("topic_probability", ascending=False)
            .head(top_n_headlines)["headline_clean"]
            .astype(str)
            .tolist()
        )
        summary_text = " | ".join(top_words + reps)

        rows.append(
            {
                "topic_id": topic_id,
                "topic_count": int(len(group)),
                "top_words": top_words,
                "top_word_scores": top_scores,
                "representative_headlines": reps,
                "topic_summary_text": summary_text,
                "topic_label_manual": "",
            }
        )

    return pd.DataFrame(rows)



def fit_topic_model(
    train_df: pd.DataFrame,
    embeddings: np.ndarray,
    settings: TopicModelSettings,
) -> tuple[object, dict[str, pd.DataFrame]]:
    """学習期間ニュースでBERTopicをfitする。"""
    required = {"news_id", "timestamp", "headline_clean"}
    missing = sorted(required - set(train_df.columns))
    if missing:
        raise ValueError(f"fit_topic_model 入力カラム不足: {missing}")

    docs = train_df["headline_clean"].fillna("").astype(str).tolist()
    if len(docs) != len(embeddings):
        raise ValueError("train_df と embeddings の行数が一致しません。")

    topic_model = _build_topic_model(settings)
    topics, probs = topic_model.fit_transform(docs, embeddings=embeddings)

    assignments = _build_assignments(train_df, topics, probs)
    topic_summary = _build_topic_summary(assignments, topic_model, settings.top_n_headlines)

    outlier_ratio = float((assignments["topic_id"] == -1).mean()) if len(assignments) > 0 else np.nan
    outlier_stats = pd.DataFrame(
        [{"n_docs": int(len(assignments)), "n_outliers": int((assignments["topic_id"] == -1).sum()), "outlier_ratio": outlier_ratio}]
    )

    topic_tables = {
        "train_assignments": assignments,
        "topic_summary": topic_summary,
        "outlier_stats": outlier_stats,
    }
    return topic_model, topic_tables



def transform_topics(
    full_df: pd.DataFrame,
    topic_model,
    embeddings: np.ndarray,
) -> pd.DataFrame:
    """学習済みBERTopicで全期間に topic_id を付与する。"""
    required = {"news_id", "timestamp", "headline_clean"}
    missing = sorted(required - set(full_df.columns))
    if missing:
        raise ValueError(f"transform_topics 入力カラム不足: {missing}")

    docs = full_df["headline_clean"].fillna("").astype(str).tolist()
    topics, probs = topic_model.transform(docs, embeddings=embeddings)
    return _build_assignments(full_df, topics, probs)



def build_topic_tables(
    assignments: pd.DataFrame,
    topic_model,
    top_n_headlines: int,
) -> dict[str, pd.DataFrame]:
    topic_summary = _build_topic_summary(assignments, topic_model, top_n_headlines)
    outlier_ratio = float((assignments["topic_id"] == -1).mean()) if len(assignments) > 0 else np.nan
    outlier_stats = pd.DataFrame(
        [{"n_docs": int(len(assignments)), "n_outliers": int((assignments["topic_id"] == -1).sum()), "outlier_ratio": outlier_ratio}]
    )
    return {"topic_summary": topic_summary, "outlier_stats": outlier_stats}
