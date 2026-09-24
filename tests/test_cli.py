from __future__ import annotations

from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from kakeibo.cli import app
from kakeibo.models import Entry
from kakeibo.storage import JsonStorage


def invoke(runner: CliRunner, data_file: Path, *args: str):
    return runner.invoke(app, ["--file", str(data_file), *args])


def test_no_args_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])
    assert "Usage" in result.output


def test_add_with_defaults(runner: CliRunner, data_file: Path, storage: JsonStorage) -> None:
    result = invoke(runner, data_file, "add", "1200")
    assert result.exit_code == 0, result.output
    assert "追加:" in result.output

    [entry] = storage.load()
    assert entry.amount == 1200
    assert entry.category == "other"
    assert entry.memo == ""
    assert entry.date == date.today()


def test_add_with_all_options(runner: CliRunner, data_file: Path, storage: JsonStorage) -> None:
    result = invoke(
        runner, data_file, "add", "1200", "-c", "food", "-m", "ランチ", "-d", "2026-09-20"
    )
    assert result.exit_code == 0, result.output

    [entry] = storage.load()
    assert entry.category == "food"
    assert entry.memo == "ランチ"
    assert entry.date == date(2026, 9, 20)


def test_add_rejects_zero_amount(runner: CliRunner, data_file: Path, storage: JsonStorage) -> None:
    result = invoke(runner, data_file, "add", "0")
    assert result.exit_code == 1
    assert "エラー:" in result.output
    assert "amount" in result.output
    assert "Traceback" not in result.output
    assert storage.load() == []


def test_add_rejects_unknown_category(runner: CliRunner, data_file: Path) -> None:
    result = invoke(runner, data_file, "add", "100", "-c", "sushi")
    assert result.exit_code != 0
    assert "sushi" in result.output


def test_add_rejects_bad_date_format(runner: CliRunner, data_file: Path) -> None:
    result = invoke(runner, data_file, "add", "100", "-d", "2026/09/20")
    assert result.exit_code != 0


def test_list_sorted_by_date(
    runner: CliRunner, data_file: Path, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    result = invoke(runner, data_file, "list")
    assert result.exit_code == 0, result.output
    lines = [line for line in result.output.splitlines() if "2026-" in line]
    assert [line.split()[3] for line in lines] == ["2026-08-31", "2026-09-01", "2026-09-20"]


def test_list_filters_by_month(
    runner: CliRunner, data_file: Path, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    result = invoke(runner, data_file, "list", "--month", "2026-08")
    assert result.exit_code == 0, result.output
    assert "コーヒー" in result.output
    assert "ランチ" not in result.output


def test_summary(
    runner: CliRunner, data_file: Path, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    result = invoke(runner, data_file, "summary")
    assert result.exit_code == 0, result.output
    assert "¥81,700" in result.output
    assert "¥80,000" in result.output
    assert "¥1,700" in result.output


def test_summary_empty(runner: CliRunner, data_file: Path) -> None:
    result = invoke(runner, data_file, "summary")
    assert result.exit_code == 0, result.output
    assert "¥0" in result.output


def test_delete_by_prefix(
    runner: CliRunner, data_file: Path, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    result = invoke(runner, data_file, "delete", str(entries[0].id)[:8])
    assert result.exit_code == 0, result.output
    assert "削除:" in result.output
    assert len(storage.load()) == 2


def test_delete_not_found(
    runner: CliRunner, data_file: Path, storage: JsonStorage, entries: list[Entry]
) -> None:
    storage.save(entries)
    result = invoke(runner, data_file, "delete", "zzz")
    assert result.exit_code == 1
    assert "エラー:" in result.output
    assert len(storage.load()) == 3


def test_file_from_env_var(
    runner: CliRunner, data_file: Path, storage: JsonStorage, monkeypatch
) -> None:
    monkeypatch.setenv("KAKEIBO_FILE", str(data_file))
    result = runner.invoke(app, ["add", "100"])
    assert result.exit_code == 0, result.output
    assert len(storage.load()) == 1
