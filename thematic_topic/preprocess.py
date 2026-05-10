"""ヘッドライン前処理。"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


PREFIXES = [
    "UPDATE 1-",
    "UPDATE 2-",
    "UPDATE 3-",
    "RPT-",
    "BREAKING-",
    "BREAKINGVIEWS-",
    "BUZZ-",
    "訂正-",
    "再送-",
    "焦点：",
    "アングル：",
    "コラム：",
    "インタビュー：",
    "〔マーケットアイ〕",
    "〔需給情報〕",
]

LOW_INFORMATION_PATTERNS = [
    "東証前引け",
    "東証大引け",
    "今日の株式見通し",
    "午前の日経平均",
    "午後の日経平均",
    "外為市場",
    "需給情報",
]

_URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
_SPACE_RE = re.compile(r"\s+")



def _strip_prefixes(text: str) -> str:
    out = text
    while True:
        changed = False
        for prefix in PREFIXES:
            if out.startswith(prefix):
                out = out[len(prefix) :].lstrip(" -:：")
                changed = True
        if not changed:
            break
    return out



def _normalize_headline(text: str) -> str:
    out = unicodedata.normalize("NFKC", text)
    out = _URL_RE.sub(" ", out)
    out = _strip_prefixes(out)
    out = _SPACE_RE.sub(" ", out)
    out = out.strip()
    return out



def _is_low_information(text: str) -> bool:
    return any(pattern in text for pattern in LOW_INFORMATION_PATTERNS)



def clean_headlines(df: pd.DataFrame, mode: str = "drop", min_chars: int = 8) -> pd.DataFrame:
    """ヘッドライン正規化と低情報処理。"""
    if "headline" not in df.columns:
        raise ValueError("headline カラムが必要です。")

    if mode not in {"drop", "flag"}:
        raise ValueError("mode は 'drop' または 'flag' を指定してください。")

    out = df.copy()
    out["headline"] = out["headline"].fillna("").astype(str)
    out["headline_clean"] = out["headline"].map(_normalize_headline)
    out["low_information_flag"] = out["headline_clean"].map(_is_low_information)
    out["too_short_flag"] = out["headline_clean"].str.len() < int(min_chars)

    out = out[~out["too_short_flag"]].copy()
    if mode == "drop":
        out = out[~out["low_information_flag"]].copy()

    out = out.reset_index(drop=True)
    return out
