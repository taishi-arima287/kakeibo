"""永続化レイヤー。

保存形式を差し替えられるよう、Entry を読み書きするインターフェース (`Storage`) だけを公開する。
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol
from uuid import UUID

from pydantic import TypeAdapter

from kakeibo.models import Entry

_entries_adapter = TypeAdapter(list[Entry])


class Storage(Protocol):
    """ストレージ実装が満たすべきインターフェース。CLI / API はこの型にだけ依存する。"""

    def load(self, month: str | None = None) -> list[Entry]:
        """日付順に返す。month (YYYY-MM) を指定するとその月だけに絞り込む。"""
        ...

    def save(self, entries: list[Entry]) -> None: ...

    def add(self, entry: Entry) -> Entry: ...

    def get(self, entry_id: UUID) -> Entry | None: ...

    def find_by_id_prefix(self, prefix: str) -> list[Entry]: ...

    def delete(self, entry_id: UUID) -> Entry | None:
        """1 件削除して削除したレコードを返す。見つからなければ None。"""
        ...


def default_path() -> Path:
    """デフォルトの保存先。CLI の --file / KAKEIBO_FILE で上書きできる。"""
    return Path.home() / ".kakeibo" / "entries.json"


class JsonStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_path()

    def _read(self) -> list[Entry]:
        if not self.path.exists():
            return []
        return _entries_adapter.validate_json(self.path.read_bytes())

    def load(self, month: str | None = None) -> list[Entry]:
        entries = self._read()
        if month:
            entries = [e for e in entries if e.date.strftime("%Y-%m") == month]
        return sorted(entries, key=lambda e: e.date)

    def save(self, entries: list[Entry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(_entries_adapter.dump_json(entries, indent=2))

    def add(self, entry: Entry) -> Entry:
        entries = self._read()
        entries.append(entry)
        self.save(entries)
        return entry

    def get(self, entry_id: UUID) -> Entry | None:
        return next((e for e in self._read() if e.id == entry_id), None)

    def find_by_id_prefix(self, prefix: str) -> list[Entry]:
        return [e for e in self._read() if str(e.id).startswith(prefix)]

    def delete(self, entry_id: UUID) -> Entry | None:
        entries = self._read()
        target = next((e for e in entries if e.id == entry_id), None)
        if target is None:
            return None
        self.save([e for e in entries if e.id != entry_id])
        return target
