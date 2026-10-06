from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from kakeibo.models import Category, Entry
from kakeibo.storage import JsonStorage, default_path


def test_default_path_is_under_home() -> None:
    assert default_path() == Path.home() / ".kakeibo" / "entries.json"


def test_load_returns_empty_when_file_missing(storage: JsonStorage) -> None:
    assert storage.load() == []


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    storage = JsonStorage(tmp_path / "nested" / "dir" / "entries.json")
    storage.save([])
    assert storage.path.exists()


def test_save_and_load_roundtrip(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert storage.load() == sorted(entries, key=lambda e: e.date)


def test_load_sorted_by_date(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert [e.date.isoformat() for e in storage.load()] == [
        "2026-08-31",
        "2026-09-01",
        "2026-09-20",
    ]


def test_load_filters_by_month(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert [e.memo for e in storage.load("2026-08")] == ["コーヒー"]
    assert storage.load("2025-01") == []


def test_save_writes_readable_json(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    raw = json.loads(storage.path.read_text())
    assert raw[0] == {
        "id": str(entries[0].id),
        "amount": 1200,
        "category": "food",
        "memo": "ランチ",
        "date": "2026-09-20",
    }


def test_add_appends(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    new = Entry(amount=300, category=Category.TRANSPORT)
    assert storage.add(new) is new
    assert storage.get(new.id) == new
    assert len(storage.load()) == 4


def test_get(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert storage.get(entries[1].id) == entries[1]
    assert storage.get(uuid4()) is None


def test_find_by_id_prefix(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert storage.find_by_id_prefix(str(entries[0].id)[:8]) == [entries[0]]
    assert storage.find_by_id_prefix("no-such-id") == []
    # 空文字は全件に前方一致する
    assert len(storage.find_by_id_prefix("")) == 3


def test_delete(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    target = entries[1]
    assert storage.delete(target.id) == target
    assert storage.get(target.id) is None
    assert len(storage.load()) == 2


def test_delete_returns_none_when_not_found(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert storage.delete(uuid4()) is None
    assert len(storage.load()) == 3
