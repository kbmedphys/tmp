"""重複抑制。"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd



def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)



def deduplicate_headlines(
    df: pd.DataFrame,
    embeddings: np.ndarray | None = None,
    similarity_threshold: float = 0.92,
    window_hours: int = 24,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """2段階重複除去。"""
    required = {"timestamp", "story_id", "headline_clean", "news_id"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"重複除去に必要なカラム不足: {missing}")

    work = df.copy().reset_index(drop=True)
    work["orig_pos"] = np.arange(len(work), dtype=int)
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True, errors="coerce")
    work = work.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    work["row_id"] = work.index

    if embeddings is not None and len(embeddings) != len(df):
        raise ValueError("embeddings 行数が入力dfと一致しません。")

    removed_rows: list[dict[str, object]] = []

    # Step 1: ルールベース
    work["story_id_norm"] = work["story_id"].fillna("").astype(str).str.strip()
    non_empty_story = work["story_id_norm"] != ""
    story_dup = non_empty_story & work["story_id_norm"].duplicated(keep="first")

    combo_key = work["headline_clean"].fillna("") + "||" + work["timestamp"].astype(str)
    combo_dup = combo_key.duplicated(keep="first")
    rule_dup = story_dup | combo_dup

    for row in work[rule_dup].itertuples(index=False):
        reason = "story_id" if getattr(row, "story_id_norm") else "headline_clean+timestamp"
        removed_rows.append(
            {
                "news_id": row.news_id,
                "removed_stage": "rule",
                "reason": reason,
                "matched_news_id": None,
                "similarity": np.nan,
            }
        )

    step1 = work[~rule_dup].copy().reset_index(drop=True)

    if embeddings is None:
        dedup_df = step1.drop(columns=["row_id", "story_id_norm", "orig_pos"], errors="ignore").reset_index(drop=True)
        dedup_log = pd.DataFrame(removed_rows)
        return dedup_df, dedup_log

    # Step 2: 近似重複
    embeddings_step1 = embeddings[step1["orig_pos"].to_numpy(dtype=int)]

    keep_indices: list[int] = []
    keep_vectors: list[np.ndarray] = []
    keep_times: list[pd.Timestamp] = []
    keep_news_ids: list[str] = []

    approx_drop_mask = np.zeros(len(step1), dtype=bool)

    for i, row in enumerate(step1.itertuples(index=False)):
        current_time = row.timestamp
        current_vec = embeddings_step1[i]

        best_match_idx = -1
        best_sim = -math.inf

        for k, prev_time in enumerate(keep_times):
            if (current_time - prev_time).total_seconds() > float(window_hours * 3600):
                continue
            sim = _cosine(current_vec, keep_vectors[k])
            if sim >= similarity_threshold and sim > best_sim:
                best_sim = sim
                best_match_idx = k

        if best_match_idx >= 0:
            approx_drop_mask[i] = True
            removed_rows.append(
                {
                    "news_id": row.news_id,
                    "removed_stage": "approx",
                    "reason": f"cosine>={similarity_threshold}",
                    "matched_news_id": keep_news_ids[best_match_idx],
                    "similarity": float(best_sim),
                }
            )
        else:
            keep_indices.append(i)
            keep_vectors.append(current_vec)
            keep_times.append(current_time)
            keep_news_ids.append(row.news_id)

    dedup_df = (
        step1.iloc[~approx_drop_mask]
        .drop(columns=["row_id", "story_id_norm", "orig_pos"], errors="ignore")
        .reset_index(drop=True)
    )
    dedup_log = pd.DataFrame(removed_rows)
    return dedup_df, dedup_log
