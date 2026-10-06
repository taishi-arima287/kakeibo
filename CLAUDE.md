# CLAUDE.md

## プロジェクトの目的

家計簿アプリを題材に、モダン Python のツールチェーンを学ぶプロジェクト。
学習が目的だが、**コードは実務レベルを目指す**。現役エンジニアが実際に使う書き方・設計・ツールの使い方を学び、それに沿って実装する。

そのため Claude は次のように関わる:

- 実装する際は、実務でよく使われるイディオムや設計パターンを選ぶ。「動けばいい」書き方や入門書向けの簡略化は避ける
- 新しい概念・ライブラリの機能・設計判断を持ち込むときは、**なぜ実務でそう書くのか**を短く説明する（代替案があれば比較も添える）
- 既存コードに実務的でない箇所を見つけたら、勝手に直さず指摘して提案する

## ロードマップ

README の Phase 表が正。現在の状況と今後の予定:

1. Phase 1: CLI (Typer + Rich + Pydantic) — 完了
2. Phase 2: FastAPI + SQLModel で API 化 — **進行中** (API は完了、次は SQLModel への差し替え)
3. 品質改善: 型チェッカー (mypy / pyright) 導入、CI、テスト拡充
4. フロントエンド: API を使う Web UI
5. Phase 3: Polars + Streamlit で可視化
6. Phase 4: Claude API 連携

## コマンド

パッケージ管理・実行はすべて uv。`pip` や `python -m venv` は使わない。

```bash
uv sync                  # 依存インストール
uv run kakeibo --help    # CLI 実行
uv run fastapi dev       # API サーバー起動 (http://127.0.0.1:8000/docs)
uv run pytest            # テスト
uv run ruff check .      # lint
uv run ruff format .     # フォーマット
```

## アーキテクチャ

```
src/kakeibo/
├── models.py    # ドメインモデル (Entry / Category / Summary)。I/O はしない
├── storage.py   # 永続化 (Storage Protocol / JsonStorage)。CLI / API のことは知らない
├── cli.py       # Typer のコマンド定義と Rich での表示
└── api.py       # FastAPI のエンドポイント定義
```

- 依存の向きは `cli / api → storage → models` の一方向に保つ。逆向きの import や `cli ↔ api` の import を作らない
- Phase 2 では `storage.py` を SQLModel 実装に差し替える。`cli.py` / `api.py` を変更せずに済むよう、両者は `Storage` Protocol (`load` / `save` / `add` / `get` / `find_by_id_prefix` / `delete`) にだけ依存させる
- 金額は円の `int`。浮動小数点は使わない

## コーディング規約

- Python 3.13。型ヒントは必須で、`X | None` や `list[int]` など新しい構文を使う
- 各モジュールの先頭に `from __future__ import annotations`
- Typer の引数・オプションは `Annotated[...]` で書く
- ruff の設定 (`pyproject.toml`) に従う。行長は 100
- docstring・コメント・コミットメッセージはすべて日本語。コメントは「なぜそうしているか」が自明でない箇所にだけ書く

## テスト

- `tests/test_*.py` は `src/kakeibo/*.py` と 1:1 で対応させる
- 共通フィクスチャは `tests/conftest.py` に置く
- テストで実際の `~/.kakeibo/` に触れない。`tmp_path` を使った `data_file` / `storage` フィクスチャを使う
- CLI のテストは `typer.testing.CliRunner` を使う
- API のテストは `client` フィクスチャ (`TestClient` + `dependency_overrides`) を使う

## 作業ルール

- コードを変更したら、完了報告の前に `uv run pytest`・`uv run ruff check .`・`uv run ruff format .` を実行し、すべて通ることを確認する
- **新しい依存を追加する前に必ず相談する**（`uv add` を勝手に実行しない）。提案するときは、なぜそのライブラリなのか、実務での採用状況、代替案を添える
- git commit / push は指示があるときだけ行う
- ユーザーとの会話は日本語で行う
