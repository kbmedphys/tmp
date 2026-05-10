"""入出力とスキーマ検証。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml


THEME_REQUIRED_COLUMNS = [
    "theme_id",
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


HOLDINGS_REQUIRED_COLUMNS = ["date", "theme_id", "ticker", "weight"]
PRICES_REQUIRED_COLUMNS = ["date", "ticker", "close"]



def _load_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {path}")
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"未対応の入力形式です: {path}")



def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (int, float, bool)):
        text = str(value).strip()
        return [text] if text else []
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_as_str_list(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for sub in value.values():
            out.extend(_as_str_list(sub))
        return out
    text = str(value).strip()
    return [text] if text else []



def _join_tokens(values: list[str]) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        token = value.strip()
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return " | ".join(ordered)



def _extract_driver_negative_events_ja(revenue_drivers: Any) -> list[str]:
    if not isinstance(revenue_drivers, list):
        return []
    out: list[str] = []
    for item in revenue_drivers:
        if isinstance(item, dict):
            out.extend(_as_str_list(item.get("negative_driver_events_ja")))
    return out



def _normalize_theme_from_yaml(theme: dict[str, Any]) -> dict[str, str]:
    if not isinstance(theme, dict):
        raise ValueError("themes の各要素は object(dict) である必要があります。")

    theme_id = str(theme.get("theme_id", "")).strip()
    theme_name = str(theme.get("theme_name_ja") or theme.get("theme_name_en") or "").strip()
    theme_description = str(theme.get("description_ja") or theme.get("description_en") or "").strip()

    revenue_drivers_ja = _as_str_list(theme.get("revenue_drivers_ja"))
    positive_events_ja = _as_str_list(theme.get("positive_events_ja"))
    negative_events_ja = _as_str_list(theme.get("negative_events_ja"))

    revenue_drivers = theme.get("revenue_drivers")
    driver_negative_ja = _extract_driver_negative_events_ja(revenue_drivers)

    keyword_match_ja = _as_str_list(theme.get("keyword_match_terms_ja"))
    catalysts_ja = _as_str_list(theme.get("catalysts_ja"))

    excluded_keywords = _as_str_list(theme.get("excluded_keywords"))

    entity_linking_terms = theme.get("entity_linking_terms") if isinstance(theme.get("entity_linking_terms"), dict) else {}
    constituent_names_ja = _as_str_list(entity_linking_terms.get("company_names_ja"))

    constituent_descriptions = str(theme.get("profile_summary_ja") or theme.get("notes_for_classification") or "").strip()

    related_industries = theme.get("related_industries") if isinstance(theme.get("related_industries"), dict) else {}
    gics_industries = _as_str_list(related_industries.get("gics_industries"))
    trbc_industries = _as_str_list(related_industries.get("trbc_industries"))

    normalized = {
        "theme_id": theme_id,
        "theme_name": theme_name,
        "theme_description": theme_description,
        "positive_drivers": _join_tokens(revenue_drivers_ja + positive_events_ja),
        "negative_drivers": _join_tokens(negative_events_ja + driver_negative_ja),
        "related_keywords": _join_tokens(keyword_match_ja + catalysts_ja),
        "excluded_keywords": _join_tokens(excluded_keywords),
        "constituent_names": _join_tokens(constituent_names_ja),
        "constituent_descriptions": constituent_descriptions,
        "gics_industries": _join_tokens(gics_industries),
        "trbc_industries": _join_tokens(trbc_industries),
    }
    return normalized



def _load_theme_definitions_yaml(path: Path) -> pd.DataFrame:
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"theme_definitions YAML の構文エラー: {path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("theme_definitions YAML のルートは object(dict) である必要があります。")

    themes = raw.get("themes")
    if not isinstance(themes, list):
        raise ValueError("theme_definitions YAML には themes(list) が必要です。")

    rows = [_normalize_theme_from_yaml(theme) for theme in themes]
    df = pd.DataFrame(rows)
    missing = sorted(set(THEME_REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"theme_definitions YAML 正規化後の必須カラム不足: {missing}")

    for col in THEME_REQUIRED_COLUMNS:
        df[col] = df[col].fillna("").astype(str)

    if (df["theme_id"].str.strip() == "").any():
        raise ValueError("theme_definitions YAML に空の theme_id があります。")

    return df



def load_theme_definitions(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _load_theme_definitions_yaml(path)

    df = _load_table(path)
    missing = sorted(set(THEME_REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"theme_definitions の必須カラム不足: {missing}")
    out = df.copy()
    for col in THEME_REQUIRED_COLUMNS:
        out[col] = out[col].fillna("").astype(str)
    return out



def load_theme_holdings(path: Path) -> pd.DataFrame:
    df = _load_table(path)
    missing = sorted(set(HOLDINGS_REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"theme_holdings の必須カラム不足: {missing}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    if out["date"].isna().any():
        raise ValueError("theme_holdings.date に datetime 変換不可の値があります。")
    out["theme_id"] = out["theme_id"].astype(str)
    out["ticker"] = out["ticker"].astype(str)
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce")
    if out["weight"].isna().any():
        raise ValueError("theme_holdings.weight に数値変換不可の値があります。")
    return out



def load_prices(path: Path) -> pd.DataFrame:
    df = _load_table(path)
    missing = sorted(set(PRICES_REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"prices の必須カラム不足: {missing}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    if out["date"].isna().any():
        raise ValueError("prices.date に datetime 変換不可の値があります。")
    out["ticker"] = out["ticker"].astype(str)
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    if out["close"].isna().any():
        raise ValueError("prices.close に数値変換不可の値があります。")
    if "turnover" in out.columns:
        out["turnover"] = pd.to_numeric(out["turnover"], errors="coerce")
    return out



def load_market_turnover(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=["date", "market_turnover"])
    df = _load_table(path)
    required = ["date", "market_turnover"]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"market_turnover の必須カラム不足: {missing}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["market_turnover"] = pd.to_numeric(out["market_turnover"], errors="coerce")
    return out



def save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)



def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
