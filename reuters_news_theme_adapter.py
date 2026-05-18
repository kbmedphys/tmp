# Reuters/LSEG news ingestion adapter for the theme basket notebook
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import hashlib
import html
import re
import time
import unicodedata
from datetime import timedelta

import numpy as np
import pandas as pd


def safe_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v) for v in x if v is not None and str(v).strip() != ""]
    if isinstance(x, tuple):
        return [str(v) for v in x if v is not None and str(v).strip() != ""]
    if isinstance(x, str):
        return [x] if x.strip() else []
    return [str(x)]


def normalize_text(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = unicodedata.normalize("NFKC", str(x)).lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
NEWS_SOURCE_MODE = "lseg"   # "lseg", "csv", or "demo"
FALLBACK_TO_DEMO_IF_REUTERS_UNAVAILABLE = True

# Date range used only for Reuters/LSEG retrieval.  Keep the range modest because
# news-headline endpoints usually have per-request limits and entitlement limits.
REUTERS_START_DATE = "2025-01-01"
REUTERS_END_DATE = None      # None -> today in UTC
REUTERS_CHUNK_DAYS = 30
REUTERS_MAX_HEADLINES_PER_REQUEST = 100
REUTERS_MAX_PAGES_PER_QUERY = 20
REUTERS_FETCH_STORY_BODY = False   # Set True only if your entitlement permits story retrieval.
REUTERS_REQUEST_SLEEP_SEC = 0.15

# Optional CSV path.  Expected minimum columns are date/published_at + headline.
# Optional columns: body, story_id, url, source_type, provider.
REUTERS_CSV_PATH = Path("reuters_news.csv")

# Optional LSEG session settings.  If LSEG_APP_KEY is None, ld.open_session() uses
# the default Workspace/Desktop or Platform configuration.
LSEG_APP_KEY = None
LSEG_CONFIG_NAME = None


def _coalesce_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return the first existing column, robust to case and punctuation differences."""
    norm_to_col = {
        re.sub(r"[^a-z0-9]", "", str(c).lower()): c
        for c in df.columns
    }
    for cand in candidates:
        key = re.sub(r"[^a-z0-9]", "", cand.lower())
        if key in norm_to_col:
            return norm_to_col[key]
    return None


def _strip_html_to_text(x: Any) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    s = html.unescape(str(x))
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _stable_news_id(*parts: Any, prefix: str = "RTRS") -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]}"


def standardize_news_df(
    raw_df: pd.DataFrame,
    default_source_type: str = "wire",
    provider: str = "Reuters",
) -> pd.DataFrame:
    """
    Convert arbitrary Reuters/LSEG/CSV headline data into the schema used by this notebook.

    Required output columns:
      news_id, date, headline, body, source_type, news_text
    Additional audit columns are preserved when available:
      published_at, story_id, url, provider, lseg_query, theme_query_id
    """
    out_cols = [
        "news_id", "date", "published_at", "headline", "body", "source_type",
        "provider", "story_id", "url", "theme_query_id", "lseg_query", "news_text",
    ]
    if raw_df is None or len(raw_df) == 0:
        return pd.DataFrame(columns=out_cols)

    df = raw_df.copy().reset_index()

    headline_col = _coalesce_col(df, ["headline", "headLine", "title", "subject", "text"])
    body_col = _coalesce_col(df, ["body", "story", "storyText", "story_text", "summary", "description"])
    date_col = _coalesce_col(df, ["published_at", "versionCreated", "created", "timestamp", "date", "datetime", "time"])
    story_col = _coalesce_col(df, ["storyId", "story_id", "storyid", "news_id", "id"])
    url_col = _coalesce_col(df, ["url", "link", "permalink"])
    source_col = _coalesce_col(df, ["source_type", "sourceType", "source", "sourceCode", "provider"])

    if headline_col is None:
        raise ValueError("News data must contain a headline/title column.")

    out = pd.DataFrame(index=df.index)
    out["headline"] = df[headline_col].fillna("").astype(str).map(_strip_html_to_text)
    out["body"] = df[body_col].fillna("").astype(str).map(_strip_html_to_text) if body_col else ""

    if date_col is not None:
        published = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    else:
        published = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    out["published_at"] = published.dt.tz_convert(None)
    out["date"] = out["published_at"].dt.normalize()

    # If a CSV only had date-like strings and parsing failed for some rows, leave only valid rows.
    out = out[out["headline"].str.len() > 0].copy()
    out = out[out["date"].notna()].copy()

    if story_col:
        out["story_id"] = df.loc[out.index, story_col].fillna("").astype(str)
    else:
        out["story_id"] = ""
    out["url"] = df.loc[out.index, url_col].fillna("").astype(str) if url_col else ""
    recognized_source_types = {"company_disclosure", "exchange", "regulator", "major_media", "wire", "blog", "social"}
    out["source_type"] = default_source_type
    if source_col:
        src = df.loc[out.index, source_col].fillna("").astype(str).map(lambda x: normalize_text(x).replace(" ", "_"))
        out["source_type"] = src.where(src.isin(recognized_source_types), default_source_type)
    out["provider"] = provider

    for c in ["theme_query_id", "lseg_query"]:
        out[c] = df.loc[out.index, c].astype(str) if c in df.columns else ""

    def _row_id(row: pd.Series) -> str:
        sid = str(row.get("story_id", "")).strip()
        if sid:
            return sid if sid.startswith("RTRS_") else f"RTRS_{sid}"
        return _stable_news_id(row.get("published_at"), row.get("headline"), row.get("url"))

    out["news_id"] = out.apply(_row_id, axis=1)
    out["news_text"] = (out["headline"].fillna("") + "。" + out["body"].fillna("")).map(normalize_text)

    # Deduplicate syndicated repeats and repeated query hits.
    dedupe_keys = ["story_id"] if out["story_id"].replace("", np.nan).notna().any() else ["date", "headline"]
    out = out.sort_values(["date", "headline"]).drop_duplicates(dedupe_keys, keep="first")
    return out[out_cols].reset_index(drop=True)


def _lseg_datetime_string(x: Any, is_end: bool = False) -> str:
    ts = pd.Timestamp.utcnow() if x is None else pd.Timestamp(x)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    if is_end:
        ts = ts + pd.Timedelta(hours=23, minutes=59, seconds=59) if ts.time() == pd.Timestamp(ts.date()).time() else ts
    return ts.strftime("%Y-%m-%dT%H:%M:%S")


def _date_chunks(start: Any, end: Any, chunk_days: int) -> Iterable[Tuple[pd.Timestamp, pd.Timestamp]]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp.utcnow().tz_convert(None).normalize() if end is None else pd.Timestamp(end)
    if start_ts.tzinfo is not None:
        start_ts = start_ts.tz_convert(None)
    if end_ts.tzinfo is not None:
        end_ts = end_ts.tz_convert(None)
    cur = start_ts.normalize()
    end_ts = end_ts.normalize()
    while cur <= end_ts:
        nxt = min(cur + pd.Timedelta(days=max(int(chunk_days), 1) - 1), end_ts)
        yield cur, nxt
        cur = nxt + pd.Timedelta(days=1)


def _is_likely_english_or_ric_term(term: Any) -> bool:
    s = str(term).strip()
    if len(s) < 2:
        return False
    if re.match(r"^R?:?[A-Za-z0-9_.-]+$", s):
        return True
    # For Reuters English news queries, prefer mostly-ASCII English phrases.
    ascii_chars = "".join(ch for ch in s if ord(ch) < 128)
    ascii_ratio = len(ascii_chars) / max(len(s), 1)
    return ascii_ratio >= 0.70 and bool(re.search(r"[A-Za-z0-9]", s))


def _quote_lseg_term(term: str) -> str:
    s = str(term).strip()
    s = re.sub(r"[\n\r\t]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    # Keep R:RIC operators as-is.
    if re.match(r"^R:[A-Za-z0-9_.-]+$", s):
        return s
    # Remove characters likely to break a simple news-query expression.
    s = re.sub(r"[^A-Za-z0-9_ .,&+\-/]", " ", s).strip()
    s = re.sub(r"\s+", " ", s)
    if not s:
        return ""
    return f'"{s}"' if " " in s else s


def build_reuters_lseg_queries(
    theme_df: pd.DataFrame,
    holdings_df: pd.DataFrame,
    max_keywords_per_theme: int = 12,
    include_global_query: bool = False,
) -> Dict[str, str]:
    """
    Build LSEG News Monitor-style query strings for Reuters English headlines.

    The query combines:
      - R:<RIC> expressions from theme holdings
      - English keywords from theme profile fields
      - Source:RTRS and Language:LEN filters
    """
    queries: Dict[str, str] = {}
    for _, t in theme_df.iterrows():
        tid = str(t["theme_id"])
        ric_terms = []
        if holdings_df is not None and len(holdings_df) > 0:
            for ric in holdings_df.loc[holdings_df["theme_id"] == tid, "ticker"].dropna().astype(str).unique():
                ric = ric.strip()
                if ric:
                    ric_terms.append(f"R:{ric}")

        keyword_terms: List[str] = []
        for field in ["theme_name_en", "profile_summary_en", "description_en"]:
            val = str(t.get(field, "")).strip()
            # Long descriptions are too broad for query strings; use nouns from explicit keyword list below instead.
            if field == "theme_name_en" and _is_likely_english_or_ric_term(val):
                keyword_terms.append(val)
        for kw in safe_list(t.get("theme_keywords")):
            if _is_likely_english_or_ric_term(kw):
                keyword_terms.append(kw)

        # Stable de-duplication while preserving order.
        seen = set()
        keyword_terms = [x for x in keyword_terms if not (x.lower() in seen or seen.add(x.lower()))]
        keyword_terms = keyword_terms[:max_keywords_per_theme]

        pieces = [_quote_lseg_term(x) for x in (ric_terms + keyword_terms)]
        pieces = [p for p in pieces if p]
        if pieces:
            expr = " OR ".join(pieces)
            queries[tid] = f"({expr}) AND Language:LEN AND Source:RTRS"

    if include_global_query:
        queries["__global_reuters__"] = "Language:LEN AND Source:RTRS"
    return queries


def _open_lseg_session(app_key: Optional[str] = None, config_name: Optional[str] = None):
    try:
        import lseg.data as ld
    except ImportError as exc:
        raise ImportError(
            "lseg-data is not installed. Install with `%pip install -U lseg-data` "
            "and run inside an entitled LSEG Workspace/Desktop or Platform session."
        ) from exc

    kwargs: Dict[str, Any] = {}
    if app_key:
        kwargs["app_key"] = app_key
    if config_name:
        kwargs["config_name"] = config_name
    try:
        ld.open_session(**kwargs)
    except TypeError:
        # Older versions may not accept empty kwargs or config_name.
        ld.open_session(app_key=app_key) if app_key else ld.open_session()
    return ld


def _extract_next_cursor_from_lseg_response(response: Any) -> str:
    raw = getattr(getattr(response, "data", None), "raw", None)
    if raw is None:
        return ""
    candidates = raw if isinstance(raw, list) else [raw]
    for obj in candidates:
        if isinstance(obj, dict):
            meta = obj.get("meta", {}) or {}
            nxt = meta.get("next", "")
            if nxt:
                return str(nxt)
    return ""


def _fetch_lseg_headlines_paginated(
    query: str,
    date_from: str,
    date_to: str,
    count: int = 100,
    max_pages: int = 20,
) -> pd.DataFrame:
    from lseg.data.content import news as lseg_news

    frames: List[pd.DataFrame] = []
    cursor = ""
    page = 0
    while page < max_pages:
        kwargs = {
            "query": query,
            "date_from": date_from,
            "date_to": date_to,
            "count": min(int(count), 100),
        }
        if cursor:
            kwargs["extended_params"] = {"cursor": cursor}
        definition = lseg_news.headlines.Definition(**kwargs)
        response = definition.get_data()
        df_page = getattr(getattr(response, "data", None), "df", None)
        if df_page is not None and len(df_page) > 0:
            frames.append(df_page.copy())
        cursor = _extract_next_cursor_from_lseg_response(response)
        page += 1
        if not cursor:
            break
        time.sleep(REUTERS_REQUEST_SLEEP_SEC)
    return pd.concat(frames, ignore_index=False) if frames else pd.DataFrame()


def _fetch_lseg_headlines_access_layer(
    ld: Any,
    query: str,
    date_from: str,
    date_to: str,
    count: int = 100,
) -> pd.DataFrame:
    # Access layer is simpler but may not expose cursor pagination in some versions.
    return ld.news.get_headlines(
        query=query,
        start=date_from,
        end=date_to,
        count=min(int(count), 100),
    )


def _fetch_lseg_story_text(ld: Any, story_id: str) -> str:
    if not story_id:
        return ""
    try:
        story = ld.news.get_story(story_id, format=ld.news.Format.TEXT)
    except Exception:
        story = ld.news.get_story(story_id)
    return _strip_html_to_text(story)


def fetch_reuters_news_from_lseg(
    theme_df: pd.DataFrame,
    holdings_df: pd.DataFrame,
    start: Any = REUTERS_START_DATE,
    end: Any = REUTERS_END_DATE,
    app_key: Optional[str] = LSEG_APP_KEY,
    config_name: Optional[str] = LSEG_CONFIG_NAME,
    include_story_body: bool = REUTERS_FETCH_STORY_BODY,
    chunk_days: int = REUTERS_CHUNK_DAYS,
    count_per_request: int = REUTERS_MAX_HEADLINES_PER_REQUEST,
    max_pages_per_query: int = REUTERS_MAX_PAGES_PER_QUERY,
    use_pagination: bool = True,
) -> pd.DataFrame:
    """Fetch Reuters headlines from an entitled LSEG session and return notebook-ready news_df."""
    ld = _open_lseg_session(app_key=app_key, config_name=config_name)
    queries = build_reuters_lseg_queries(theme_df, holdings_df)
    if not queries:
        raise ValueError("No Reuters/LSEG queries were built from theme_df/holdings_df.")

    frames: List[pd.DataFrame] = []
    for theme_query_id, query in queries.items():
        for start_ts, end_ts in _date_chunks(start, end, chunk_days):
            date_from = _lseg_datetime_string(start_ts)
            date_to = _lseg_datetime_string(end_ts, is_end=True)
            try:
                if use_pagination:
                    raw = _fetch_lseg_headlines_paginated(
                        query=query,
                        date_from=date_from,
                        date_to=date_to,
                        count=count_per_request,
                        max_pages=max_pages_per_query,
                    )
                else:
                    raw = _fetch_lseg_headlines_access_layer(
                        ld=ld,
                        query=query,
                        date_from=date_from,
                        date_to=date_to,
                        count=count_per_request,
                    )
            except Exception as exc:
                print(f"LSEG query failed for {theme_query_id} {date_from}..{date_to}: {exc}")
                continue
            if raw is not None and len(raw) > 0:
                raw = raw.copy()
                raw["theme_query_id"] = theme_query_id
                raw["lseg_query"] = query
                frames.append(raw)
            time.sleep(REUTERS_REQUEST_SLEEP_SEC)

    if not frames:
        return standardize_news_df(pd.DataFrame(), provider="Reuters")

    news = standardize_news_df(pd.concat(frames, ignore_index=False), provider="Reuters")

    if include_story_body and len(news) > 0:
        body_cache: Dict[str, str] = {}
        for sid in news["story_id"].dropna().astype(str).unique():
            clean_sid = sid.replace("RTRS_", "", 1)
            if clean_sid and clean_sid not in body_cache:
                try:
                    body_cache[clean_sid] = _fetch_lseg_story_text(ld, clean_sid)
                except Exception as exc:
                    print(f"Story retrieval failed for {clean_sid}: {exc}")
                    body_cache[clean_sid] = ""
                time.sleep(REUTERS_REQUEST_SLEEP_SEC)
        news["body"] = news.apply(
            lambda r: body_cache.get(str(r["story_id"]).replace("RTRS_", "", 1), r["body"]),
            axis=1,
        )
        news["news_text"] = (news["headline"].fillna("") + "。" + news["body"].fillna("")).map(normalize_text)
    return news


def load_reuters_news_from_csv(path: Path = REUTERS_CSV_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Reuters CSV not found: {path.resolve()}")
    raw = pd.read_csv(path)
    return standardize_news_df(raw, provider="Reuters")


def load_news_for_pipeline(
    mode: str,
    demo_news_df: pd.DataFrame,
    theme_df: pd.DataFrame,
    holdings_df: pd.DataFrame,
) -> pd.DataFrame:
    mode = str(mode).lower().strip()
    if mode == "demo":
        return standardize_news_df(demo_news_df, provider="Demo")
    if mode == "csv":
        return load_reuters_news_from_csv(REUTERS_CSV_PATH)
    if mode == "lseg":
        try:
            df = fetch_reuters_news_from_lseg(theme_df=theme_df, holdings_df=holdings_df)
            if len(df) == 0:
                raise RuntimeError("LSEG returned no Reuters headlines for the configured queries/date range.")
            return df
        except Exception as exc:
            if FALLBACK_TO_DEMO_IF_REUTERS_UNAVAILABLE:
                print("Reuters/LSEG ingestion was not available; falling back to demo news.")
                print(f"Reason: {exc}")
                return standardize_news_df(demo_news_df, provider="Demo")
            raise
    raise ValueError("NEWS_SOURCE_MODE must be one of: 'lseg', 'csv', 'demo'.")


