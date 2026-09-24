from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from kakeibo.models import Category, Entry, Summary


def test_entry_defaults() -> None:
    entry = Entry(amount=100, category=Category.FOOD)
    assert entry.memo == ""
    assert entry.date == date.today()
    assert entry.id is not None


def test_entry_ids_are_unique() -> None:
    a = Entry(amount=1, category=Category.OTHER)
    b = Entry(amount=1, category=Category.OTHER)
    assert a.id != b.id


@pytest.mark.parametrize("amount", [0, -1])
def test_entry_rejects_non_positive_amount(amount: int) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Entry(amount=amount, category=Category.FOOD)
    assert exc_info.value.errors()[0]["loc"] == ("amount",)


def test_entry_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        Entry.model_validate({"amount": 1, "category": "sushi"})


def test_entry_json_roundtrip() -> None:
    original = Entry(amount=1200, category=Category.FOOD, memo="ランチ", date=date(2026, 9, 20))
    restored = Entry.model_validate_json(original.model_dump_json())
    assert restored == original


def test_summary_from_entries(entries: list[Entry]) -> None:
    s = Summary.from_entries(entries)
    assert s.total == 81700
    assert s.by_category == {Category.FOOD: 1700, Category.HOUSING: 80000}


def test_summary_from_empty() -> None:
    s = Summary.from_entries([])
    assert s.total == 0
    assert s.by_category == {}
