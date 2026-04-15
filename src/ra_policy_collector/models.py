"""データモデル定義"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class PolicyItem:
    """収集した政策情報1件を表すデータモデル"""

    title: str
    url: str
    source: str  # e.g. "mext", "jst", "jsps", "csti"
    source_name: str  # e.g. "文部科学省", "JST"
    published_date: Optional[str] = None  # YYYY-MM-DD or original text
    deadline: Optional[str] = None
    category: Optional[str] = None  # "公募", "報道発表", "会議" etc.
    description: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CollectionResult:
    """1ソースからの収集結果"""

    source: str
    source_name: str
    items: list[PolicyItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def count(self) -> int:
        return len(self.items)


def load_previous_items(data_dir: Path, source: str) -> list[dict]:
    """前回の収集データを読み込む"""
    path = data_dir / f"{source}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_items(data_dir: Path, source: str, items: list[PolicyItem]) -> Path:
    """収集データを保存する"""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / f"{source}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            [item.to_dict() for item in items],
            f,
            ensure_ascii=False,
            indent=2,
        )
    return path


def detect_new_items(
    current: list[PolicyItem], previous: list[dict]
) -> list[PolicyItem]:
    """前回と比較して新規アイテムを検出する"""
    prev_urls = {item["url"] for item in previous if "url" in item}
    return [item for item in current if item.url not in prev_urls]
