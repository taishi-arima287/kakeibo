"""Web API エントリポイント。

`uv run fastapi dev` で起動する (エントリポイントは pyproject.toml の [tool.fastapi])。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status

from kakeibo.models import Entry, EntryCreate, Summary
from kakeibo.storage import JsonStorage, Storage


def get_storage() -> Storage:
    """リクエストごとのストレージ。テストでは dependency_overrides で差し替える。"""
    path = os.environ.get("KAKEIBO_FILE")
    return JsonStorage(Path(path) if path else None)


StorageDep = Annotated[Storage, Depends(get_storage)]
MonthQuery = Annotated[
    str | None,
    Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="YYYY-MM で絞り込み"),
]


entries_router = APIRouter(prefix="/entries", tags=["entries"])


# ストレージはブロッキング I/O なので async def ではなく def で定義する。
# def のエンドポイントは FastAPI がスレッドプールで実行するため、イベントループを止めない。
@entries_router.post("", status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, storage: StorageDep) -> Entry:
    return storage.add(Entry.model_validate(payload.model_dump()))


@entries_router.get("")
def list_entries(storage: StorageDep, month: MonthQuery = None) -> list[Entry]:
    return storage.load(month)


# ルートは定義順に照合されるため、/{entry_id} より先に定義する
@entries_router.get("/summary")
def read_summary(storage: StorageDep, month: MonthQuery = None) -> Summary:
    return Summary.from_entries(storage.load(month))


@entries_router.get("/{entry_id}")
def read_entry(entry_id: UUID, storage: StorageDep) -> Entry:
    entry = storage.get(entry_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@entries_router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: UUID, storage: StorageDep) -> None:
    if storage.delete(entry_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Entry not found")


app = FastAPI(title="kakeibo API", description="家計簿 API")
app.include_router(entries_router, prefix="/api/v1")
