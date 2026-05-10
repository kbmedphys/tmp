"""トピックレポート用の集計・可視化ヘルパー。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def build_topic_top_headline_table(
    topic_assignments: pd.DataFrame,
    exclude_outlier: bool = True,
    headline_col: str = "headline_clean",
) -> pd.DataFrame:
    """各topicで構成比率(topic_probability)が最大の見出しを返す。"""
    required = {"topic_id", "topic_probability"}
    missing = sorted(required - set(topic_assignments.columns))
    if missing:
        raise ValueError(f"topic_assignments 必須カラム不足: {missing}")

    use_headline_col = headline_col if headline_col in topic_assignments.columns else "headline"
    if use_headline_col not in topic_assignments.columns:
        raise ValueError("見出し列が見つかりません。headline_clean または headline が必要です。")

    work = topic_assignments.copy()
    if exclude_outlier:
        work = work[work["topic_id"] != -1].copy()
    if work.empty:
        return pd.DataFrame(columns=["topic_id", "composition_ratio", "headline"])

    work = work.dropna(subset=["topic_probability"]).copy()
    if work.empty:
        return pd.DataFrame(columns=["topic_id", "composition_ratio", "headline"])

    work["_ts_sort"] = pd.to_datetime(work["timestamp"], utc=True, errors="coerce") if "timestamp" in work.columns else pd.NaT
    work["_ts_sort"] = work["_ts_sort"].fillna(pd.Timestamp.max.tz_localize("UTC"))
    work["_news_sort"] = work["news_id"].astype(str) if "news_id" in work.columns else ""

    work = work.sort_values(
        by=["topic_id", "topic_probability", "_ts_sort", "_news_sort"],
        ascending=[True, False, True, True],
    )
    best = work.drop_duplicates(subset=["topic_id"], keep="first").copy()

    out = best[["topic_id", "topic_probability", use_headline_col]].copy()
    out = out.rename(columns={"topic_probability": "composition_ratio", use_headline_col: "headline"})
    out["headline"] = out["headline"].fillna("").astype(str)
    out = out.sort_values("topic_id").reset_index(drop=True)
    return out


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _resolve_japanese_font_path(font_path: str | None = None) -> str:
    if font_path is not None:
        path = Path(font_path)
        if not path.exists():
            raise ValueError(f"font_path が見つかりません: {font_path}")
        return str(path)

    candidates = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise ValueError("日本語フォントが見つかりません。font_path を明示指定してください。")


def _make_word_weights(words: list[str], scores: list[float] | None) -> dict[str, float]:
    clean_words = [str(w).strip() for w in words if str(w).strip()]
    if not clean_words:
        return {}

    if scores is not None and len(scores) >= len(clean_words):
        out: dict[str, float] = {}
        for w, s in zip(clean_words, scores):
            try:
                score = float(s)
            except Exception:
                score = 0.0
            out[w] = max(score, 1e-6)
        return out

    out = {}
    for idx, w in enumerate(clean_words, start=1):
        out[w] = 1.0 / float(idx)
    return out


def make_topic_wordclouds(
    topic_summary_df: pd.DataFrame,
    max_topics: int | None = None,
    font_path: str | None = None,
) -> dict[int, Any]:
    """topic_summary から topic別 WordCloud オブジェクトを生成する。"""
    required = {"topic_id", "top_words"}
    missing = sorted(required - set(topic_summary_df.columns))
    if missing:
        raise ValueError(f"topic_summary 必須カラム不足: {missing}")

    try:
        from wordcloud import WordCloud
    except Exception as exc:
        raise ValueError("wordcloud が利用できません。依存関係をインストールしてください。") from exc

    font = _resolve_japanese_font_path(font_path)
    topic_df = topic_summary_df.copy()
    if "topic_count" in topic_df.columns:
        topic_df = topic_df.sort_values("topic_count", ascending=False)
    if max_topics is not None:
        topic_df = topic_df.head(int(max_topics))

    cloud_map: dict[int, Any] = {}
    for row in topic_df.itertuples(index=False):
        topic_id = int(getattr(row, "topic_id"))
        words = [str(x) for x in _as_list(getattr(row, "top_words", []))]
        scores_obj = getattr(row, "top_word_scores", None) if "top_word_scores" in topic_df.columns else None
        scores = [float(x) for x in _as_list(scores_obj)] if scores_obj is not None else None
        weights = _make_word_weights(words, scores)
        if not weights:
            continue

        wc = WordCloud(
            width=1200,
            height=700,
            background_color="white",
            collocations=False,
            font_path=font,
        ).generate_from_frequencies(weights)
        cloud_map[topic_id] = wc

    return cloud_map
