"""永続化レイヤー。

保存形式を差し替えられるよう、Entry のリストを読み書きするインターフェースだけを公開する。
"""

from __future__ import annotations

from pathlib import Path

from pydantic import TypeAdapter

from kakeibo.models import Entry

_entries_adapter = TypeAdapter(list[Entry])


def default_path() -> Path:
    """デフォルトの保存先。CLI の --file / KAKEIBO_FILE で上書きできる。"""
    return Path.home() / ".kakeibo" / "entries.json"


class JsonStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_path()

    def load(self) -> list[Entry]:
        if not self.path.exists():
            return []
        return _entries_adapter.validate_json(self.path.read_bytes())

    def save(self, entries: list[Entry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(_entries_adapter.dump_json(entries, indent=2))

    def add(self, entry: Entry) -> Entry:
        entries = self.load()
        entries.append(entry)
        self.save(entries)
        return entry

    def delete(self, entry_id_prefix: str) -> Entry | None:
        """ID の先頭一致で 1 件削除する。見つからなければ None。"""
        entries = self.load()
        matched = [e for e in entries if str(e.id).startswith(entry_id_prefix)]
        if len(matched) != 1:
            return None
        target = matched[0]
        self.save([e for e in entries if e.id != target.id])
        return target
