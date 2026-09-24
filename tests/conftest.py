"""pytest 共通フィクスチャ。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from kakeibo.models import Category, Entry
from kakeibo.storage import JsonStorage


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    """テスト専用のデータファイル。実際の ~/.kakeibo には触れない。"""
    return tmp_path / "entries.json"


@pytest.fixture
def storage(data_file: Path) -> JsonStorage:
    return JsonStorage(data_file)


@pytest.fixture
def entries() -> list[Entry]:
    """月またぎ・複数カテゴリを含むサンプルデータ。"""
    return [
        Entry(amount=1200, category=Category.FOOD, memo="ランチ", date=date(2026, 9, 20)),
        Entry(amount=80000, category=Category.HOUSING, date=date(2026, 9, 1)),
        Entry(amount=500, category=Category.FOOD, memo="コーヒー", date=date(2026, 8, 31)),
    ]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
