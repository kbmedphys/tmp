"""共通ユーティリティ。"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Iterable

import pandas as pd



def hash_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()



def hash_values(values: Iterable[str]) -> str:
    joined = "||".join(values)
    return hash_text(joined)



def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)



def find_first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(f"候補カラムが見つかりません: {candidates}")
