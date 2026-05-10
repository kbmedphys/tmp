"""LSEG headlines 取得と正規化。"""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PipelineConfig
from .utils import find_first_existing_col, hash_values


TIMESTAMP_CANDIDATES = ["versionCreated", "created", "published", "firstCreated", "date"]
HEADLINE_CANDIDATES = ["headline", "text", "storyHeadline", "headlineText", "title"]
STORY_ID_CANDIDATES = ["storyId", "story_id", "storyID", "id", "news_id"]
SOURCE_CANDIDATES = ["sourceCode", "source", "provider", "sourceName"]


class HeadlineFetchError(RuntimeError):
    """LSEG取得時のエラー。"""



def normalize_headlines_df(
    raw_df: pd.DataFrame,
    query: str = "",
    request_start: str | None = None,
    request_end: str | None = None,
    retrieved_at_utc: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """LSEG headline DataFrame を標準スキーマへ変換する。"""
    if raw_df is None:
        raise ValueError("raw_df が None です。")

    df = raw_df.copy()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "news_id",
                "story_id",
                "timestamp",
                "headline",
                "source",
                "query",
                "request_start",
                "request_end",
                "retrieved_at_utc",
            ]
        )

    if df.index.name == "versionCreated":
        df = df.reset_index()
        time_col = "versionCreated"
    elif isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
        time_col = str(df.columns[0])
    else:
        df = df.reset_index()
        if "versionCreated" in df.columns:
            time_col = "versionCreated"
        else:
            time_col = find_first_existing_col(df, TIMESTAMP_CANDIDATES)

    headline_col = find_first_existing_col(df, HEADLINE_CANDIDATES)
    story_col = find_first_existing_col(df, STORY_ID_CANDIDATES)
    source_col = find_first_existing_col(df, SOURCE_CANDIDATES)

    out = pd.DataFrame()
    out["story_id"] = df[story_col].fillna("").astype(str)
    out["headline"] = df[headline_col].fillna("").astype(str)
    out["source"] = df[source_col].fillna("").astype(str)
    out["timestamp"] = pd.to_datetime(df[time_col], errors="coerce", utc=True)

    out = out.dropna(subset=["timestamp"]).reset_index(drop=True)

    out["query"] = str(query)
    out["request_start"] = request_start
    out["request_end"] = request_end
    if retrieved_at_utc is None:
        retrieved_at_utc = pd.Timestamp.now("UTC")
    out["retrieved_at_utc"] = pd.to_datetime(retrieved_at_utc, utc=True)

    out["news_id"] = out.apply(
        lambda r: hash_values(
            [
                str(r["story_id"]),
                str(r["timestamp"]),
                str(r["headline"]),
                str(r["source"]),
            ]
        )[:20],
        axis=1,
    )

    out = out[
        [
            "news_id",
            "story_id",
            "timestamp",
            "headline",
            "source",
            "query",
            "request_start",
            "request_end",
            "retrieved_at_utc",
        ]
    ]
    return out



def _resolve_order_by(order_by: str):
    import lseg.data as ld

    if hasattr(ld.news.SortOrder, order_by):
        return getattr(ld.news.SortOrder, order_by)
    return order_by



def _make_chunk_windows(start: pd.Timestamp, end: pd.Timestamp, chunk_days: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    windows: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    cursor = start
    while cursor < end:
        next_cursor = min(cursor + timedelta(days=chunk_days), end)
        windows.append((cursor, next_cursor))
        cursor = next_cursor
    return windows



def fetch_headlines(config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """LSEGからヘッドラインを取得し、raw と正規化テーブルを返す。"""
    import lseg.data as ld

    fetch = config.lseg_fetch
    cache_dir = config.resolve_path(fetch.cache_dir)
    if cache_dir is None:
        raise ValueError("cache_dir が設定されていません。")
    cache_dir.mkdir(parents=True, exist_ok=True)

    start = pd.to_datetime(fetch.start, utc=True)
    end = pd.to_datetime(fetch.end, utc=True)
    if pd.isna(start) or pd.isna(end) or start >= end:
        raise ValueError("lseg_fetch.start/end の指定が不正です。")

    order_by = _resolve_order_by(fetch.order_by)
    chunk_windows = _make_chunk_windows(start, end, int(fetch.chunk_days))
    raw_frames: list[pd.DataFrame] = []
    normalized_frames: list[pd.DataFrame] = []

    for chunk_start, chunk_end in chunk_windows:
        chunk_key = hash_values(
            [
                fetch.query,
                chunk_start.isoformat(),
                chunk_end.isoformat(),
                str(fetch.count),
                str(fetch.order_by),
            ]
        )[:16]
        raw_path = cache_dir / f"headlines_raw_{chunk_key}.parquet"
        meta_path = cache_dir / f"headlines_raw_{chunk_key}.json"

        if raw_path.exists() and not fetch.force_refresh:
            chunk_raw = pd.read_parquet(raw_path)
            if "_index_versionCreated" in chunk_raw.columns:
                chunk_raw = chunk_raw.set_index("_index_versionCreated")
                chunk_raw.index.name = "versionCreated"
        else:
            try:
                chunk_raw = ld.news.get_headlines(
                    query=fetch.query,
                    count=int(fetch.count),
                    start=chunk_start.to_pydatetime(),
                    end=chunk_end.to_pydatetime(),
                    order_by=order_by,
                )
            except Exception as exc:
                raise HeadlineFetchError(
                    "LSEG headlines 取得に失敗しました。認証情報とセッション設定を確認してください。"
                ) from exc

            to_save = chunk_raw.copy()
            if isinstance(to_save.index, pd.DatetimeIndex) or to_save.index.name == "versionCreated":
                index_name = to_save.index.name or "index"
                to_save = to_save.reset_index().rename(columns={index_name: "_index_versionCreated"})
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            to_save.to_parquet(raw_path, index=False)
            meta_path.write_text(
                json.dumps(
                    {
                        "query": fetch.query,
                        "start": chunk_start.isoformat(),
                        "end": chunk_end.isoformat(),
                        "count": fetch.count,
                        "order_by": fetch.order_by,
                        "lseg_fetch": asdict(fetch),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        raw_frames.append(chunk_raw)
        normalized_frames.append(
            normalize_headlines_df(
                chunk_raw,
                query=fetch.query,
                request_start=chunk_start.isoformat(),
                request_end=chunk_end.isoformat(),
                retrieved_at_utc=pd.Timestamp.now("UTC"),
            )
        )

    if raw_frames:
        raw_all = pd.concat(raw_frames, axis=0)
    else:
        raw_all = pd.DataFrame()

    if normalized_frames:
        normalized_all = pd.concat(normalized_frames, ignore_index=True)
        normalized_all = normalized_all.sort_values("timestamp").drop_duplicates(subset=["news_id"], keep="first")
        normalized_all = normalized_all.reset_index(drop=True)
    else:
        normalized_all = normalize_headlines_df(pd.DataFrame())

    return raw_all, normalized_all
