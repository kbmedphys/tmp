"""埋め込み計算とキャッシュ。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from .utils import hash_text



def load_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)



def _to_vector(value: object) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value.astype(float)
    if isinstance(value, list):
        return np.array(value, dtype=float)
    return np.array([], dtype=float)



def encode_texts_with_cache(
    ids: pd.Series,
    texts: pd.Series,
    cache_path: Path,
    model_name: str,
    batch_size: int = 64,
    normalize_embeddings: bool = True,
) -> tuple[pd.DataFrame, np.ndarray]:
    """id/text 単位で埋め込みを再利用する。"""
    request = pd.DataFrame({"id": ids.astype(str), "text": texts.fillna("").astype(str)})
    request["text_hash"] = request["text"].map(hash_text)
    request["model_name"] = str(model_name)

    cache_cols = ["id", "text_hash", "model_name", "embedding"]
    if cache_path.exists():
        cache_df = pd.read_parquet(cache_path)
        missing = sorted(set(cache_cols) - set(cache_df.columns))
        if missing:
            raise ValueError(f"embedding cache 形式不正: {missing}")
    else:
        cache_df = pd.DataFrame(columns=cache_cols)

    merged = request.merge(cache_df, on=["id", "text_hash", "model_name"], how="left")
    missing_mask = merged["embedding"].isna()

    if missing_mask.any():
        model = load_model(model_name)
        encoded = model.encode(
            merged.loc[missing_mask, "text"].tolist(),
            batch_size=batch_size,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        new_cache = merged.loc[missing_mask, ["id", "text_hash", "model_name"]].copy()
        new_cache["embedding"] = [vec.astype(float).tolist() for vec in encoded]

        cache_df = pd.concat([cache_df, new_cache], ignore_index=True)
        cache_df = cache_df.drop_duplicates(subset=["id", "text_hash", "model_name"], keep="last")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_df.to_parquet(cache_path, index=False)

        merged = request.merge(cache_df, on=["id", "text_hash", "model_name"], how="left")

    vectors = np.vstack(merged["embedding"].map(_to_vector).values)
    return merged, vectors
