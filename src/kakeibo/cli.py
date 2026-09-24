"""CLI エントリポイント。"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from kakeibo.models import Category, Entry, Summary
from kakeibo.storage import JsonStorage

app = typer.Typer(help="家計簿 CLI", no_args_is_help=True)
console = Console()

FileOption = Annotated[
    Path | None,
    typer.Option("--file", "-f", envvar="KAKEIBO_FILE", help="データファイルのパス"),
]


@app.callback()
def main(ctx: typer.Context, file: FileOption = None) -> None:
    ctx.obj = JsonStorage(file)


def _storage(ctx: typer.Context) -> JsonStorage:
    return ctx.obj


def _fail(message: str) -> typer.Exit:
    """エラーを表示し、`raise _fail(...)` で送出するための Exit を返す。"""
    console.print(f"[red]エラー:[/] {message}")
    return typer.Exit(code=1)


def _format_validation_error(exc: ValidationError) -> str:
    """ValidationError を「フィールド名: メッセージ」の 1 行にまとめる。"""
    return ", ".join(
        f"{'.'.join(str(loc) for loc in err['loc']) or '(全体)'}: {err['msg']}"
        for err in exc.errors()
    )


@app.command()
def add(
    ctx: typer.Context,
    amount: Annotated[int, typer.Argument(help="金額 (円)")],
    category: Annotated[Category, typer.Option("--category", "-c")] = Category.OTHER,
    memo: Annotated[str, typer.Option("--memo", "-m")] = "",
    # Typer は date 型に未対応のため datetime で受けて .date() に変換する
    on: Annotated[
        datetime | None,
        typer.Option("--date", "-d", formats=["%Y-%m-%d"], help="YYYY-MM-DD"),
    ] = None,
) -> None:
    """支出を 1 件追加する。"""
    try:
        entry = Entry(
            amount=amount, category=category, memo=memo, date=on.date() if on else date.today()
        )
    except ValidationError as exc:
        raise _fail(_format_validation_error(exc)) from None
    _storage(ctx).add(entry)
    console.print(
        f"[green]追加:[/] {entry.date} {entry.category:<13} ¥{entry.amount:,} {entry.memo}"
    )


# 関数名を list にすると組み込みの list を隠すため、コマンド名のみ明示する
@app.command("list")
def list_entries(
    ctx: typer.Context,
    month: Annotated[str | None, typer.Option("--month", help="YYYY-MM で絞り込み")] = None,
) -> None:
    """支出を一覧表示する。"""
    entries = _storage(ctx).load()
    if month:
        entries = [e for e in entries if e.date.strftime("%Y-%m") == month]
    entries.sort(key=lambda e: e.date)

    table = Table(title=f"支出一覧 {month or ''}".strip())
    table.add_column("ID", style="dim")
    table.add_column("日付")
    table.add_column("カテゴリ")
    table.add_column("金額", justify="right")
    table.add_column("メモ")
    for e in entries:
        table.add_row(str(e.id)[:8], str(e.date), e.category, f"¥{e.amount:,}", e.memo)
    console.print(table)


@app.command()
def summary(
    ctx: typer.Context,
    month: Annotated[str | None, typer.Option("--month", help="YYYY-MM で絞り込み")] = None,
) -> None:
    """カテゴリ別の合計を表示する。"""
    entries = _storage(ctx).load()
    if month:
        entries = [e for e in entries if e.date.strftime("%Y-%m") == month]
    s = Summary.from_entries(entries)

    table = Table(title=f"カテゴリ別集計 {month or ''}".strip())
    table.add_column("カテゴリ")
    table.add_column("金額", justify="right")
    table.add_column("割合", justify="right")
    for cat, amount in sorted(s.by_category.items(), key=lambda kv: -kv[1]):
        ratio = amount / s.total * 100 if s.total else 0
        table.add_row(cat, f"¥{amount:,}", f"{ratio:.1f}%")
    table.add_section()
    table.add_row("[bold]合計[/]", f"[bold]¥{s.total:,}[/]", "")
    console.print(table)


@app.command()
def delete(
    ctx: typer.Context,
    entry_id: Annotated[str, typer.Argument(help="ID (先頭数文字でOK)")],
) -> None:
    """支出を 1 件削除する。"""
    deleted = _storage(ctx).delete(entry_id)
    if deleted is None:
        raise _fail(f"ID '{entry_id}' に一致するレコードが 1 件に定まりません")
    console.print(f"[yellow]削除:[/] {deleted.date} {deleted.category} ¥{deleted.amount:,}")


if __name__ == "__main__":
    app()
