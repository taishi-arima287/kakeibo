from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kakeibo.api import get_storage
from kakeibo.models import Entry
from kakeibo.storage import JsonStorage

BASE = "/api/v1/entries"


def test_create_entry(client: TestClient, storage: JsonStorage) -> None:
    res = client.post(
        BASE,
        json={"amount": 1200, "category": "food", "memo": "ランチ", "date": "2026-09-20"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["amount"] == 1200
    assert body["date"] == "2026-09-20"

    [entry] = storage.load()
    assert str(entry.id) == body["id"]


def test_create_entry_with_defaults(client: TestClient) -> None:
    res = client.post(BASE, json={"amount": 500, "category": "other"})
    assert res.status_code == 201, res.text
    assert res.json()["memo"] == ""
    assert res.json()["date"] == date.today().isoformat()


def test_create_entry_ignores_client_supplied_id(client: TestClient) -> None:
    given = str(uuid4())
    res = client.post(BASE, json={"id": given, "amount": 500, "category": "other"})
    assert res.status_code == 201, res.text
    assert res.json()["id"] != given


@pytest.mark.parametrize(
    "payload",
    [
        {"amount": 0, "category": "food"},
        {"amount": 100, "category": "sushi"},
        {"amount": 100},
        {"amount": 100, "category": "food", "date": "2026/09/20"},
    ],
)
def test_create_entry_rejects_invalid(
    client: TestClient, storage: JsonStorage, payload: dict[str, object]
) -> None:
    res = client.post(BASE, json=payload)
    assert res.status_code == 422
    assert storage.load() == []


def test_list_entries_sorted_by_date(
    client: TestClient, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    res = client.get(BASE)
    assert res.status_code == 200
    assert [e["date"] for e in res.json()] == ["2026-08-31", "2026-09-01", "2026-09-20"]


def test_list_entries_filters_by_month(
    client: TestClient, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    res = client.get(BASE, params={"month": "2026-08"})
    assert res.status_code == 200
    assert [e["memo"] for e in res.json()] == ["コーヒー"]


@pytest.mark.parametrize("month", ["2026-13", "2026-9", "202609"])
def test_list_entries_rejects_bad_month(client: TestClient, month: str) -> None:
    assert client.get(BASE, params={"month": month}).status_code == 422


def test_read_entry(client: TestClient, storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    res = client.get(f"{BASE}/{entries[0].id}")
    assert res.status_code == 200
    assert res.json()["memo"] == "ランチ"


def test_read_entry_not_found(client: TestClient) -> None:
    assert client.get(f"{BASE}/{uuid4()}").status_code == 404


def test_read_entry_rejects_non_uuid(client: TestClient) -> None:
    assert client.get(f"{BASE}/abc").status_code == 422


def test_delete_entry(client: TestClient, storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    res = client.delete(f"{BASE}/{entries[0].id}")
    assert res.status_code == 204
    assert res.content == b""
    assert storage.get(entries[0].id) is None


def test_delete_entry_not_found(
    client: TestClient, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    assert client.delete(f"{BASE}/{uuid4()}").status_code == 404
    assert len(storage.load()) == 3


def test_summary(client: TestClient, storage: JsonStorage, entries: list[Entry]) -> None:
    storage.save(entries)
    res = client.get(f"{BASE}/summary")
    assert res.status_code == 200
    assert res.json() == {"total": 81700, "by_category": {"food": 1700, "housing": 80000}}


def test_summary_filters_by_month(
    client: TestClient, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    res = client.get(f"{BASE}/summary", params={"month": "2026-08"})
    assert res.json() == {"total": 500, "by_category": {"food": 500}}


def test_summary_is_not_treated_as_entry_id(client: TestClient) -> None:
    # /{entry_id} より後に定義すると "summary" が UUID として検証され 422 になる
    assert client.get(f"{BASE}/summary").status_code == 200


def test_unversioned_path_is_not_found(client: TestClient) -> None:
    assert client.get("/entries").status_code == 404


def test_get_storage_uses_env_var(monkeypatch: pytest.MonkeyPatch, data_file: Path) -> None:
    monkeypatch.setenv("KAKEIBO_FILE", str(data_file))
    storage = get_storage()
    assert isinstance(storage, JsonStorage)
    assert storage.path == data_file
