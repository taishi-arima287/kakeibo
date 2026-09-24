from __future__ import annotations

import json
from pathlib import Path

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
    assert storage.load() == entries


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
    assert storage.load() == [*entries, new]


def test_delete_by_prefix(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    target = entries[1]
    deleted = storage.delete(str(target.id)[:8])
    assert deleted == target
    assert target not in storage.load()
    assert len(storage.load()) == 2


def test_delete_returns_none_when_no_match(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    assert storage.delete("no-such-id") is None
    assert len(storage.load()) == 3


def test_delete_returns_none_when_ambiguous(storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    # 空文字は全件に前方一致するので 1 件に定まらない
    assert storage.delete("") is None
    assert len(storage.load()) == 3
