# kakeibo

家計簿 CLI。モダン Python のツールチェーン (uv / Typer / Rich / Pydantic / ruff / pytest) を学ぶためのプロジェクト。

## 学習の流れ

| Phase | 内容 | 状態 |
|---|---|---|
| 1 | CLI (Typer + Rich + Pydantic) | ✅ 完了 |
| 2 | FastAPI + SQLModel で API 化 | 🚧 進行中 (API 完了 / SQLModel 未着手) |
| 3 | Polars + Streamlit で可視化 | 未着手 |
| 4 | Claude API 連携 | 未着手 |

## 必要なもの

- [uv](https://docs.astral.sh/uv/)
- Python 3.13 (`.python-version` に記載。uv が自動で用意する)

## セットアップ

```bash
uv sync
```

`.venv/` に依存が入り、`kakeibo` コマンドが使えるようになる。

## 使い方

```bash
uv run kakeibo --help
```

### 支出を追加する

```bash
uv run kakeibo add 1200 --category food --memo ランチ
uv run kakeibo add 80000 -c housing -d 2026-09-01   # 短縮オプション、日付指定
uv run kakeibo add 500                              # カテゴリ省略時は other、日付は今日
```

| オプション | 短縮 | 説明 | デフォルト |
|---|---|---|---|
| `--category` | `-c` | `food` / `housing` / `transport` / `utilities` / `entertainment` / `health` / `other` | `other` |
| `--memo` | `-m` | メモ | 空 |
| `--date` | `-d` | `YYYY-MM-DD` | 今日 |

### 一覧・集計

```bash
uv run kakeibo list                   # 全件を日付順に表示
uv run kakeibo list --month 2026-09   # 月で絞り込み
uv run kakeibo summary                # カテゴリ別の合計と割合
uv run kakeibo summary --month 2026-09
```

### 削除

```bash
uv run kakeibo delete 80e3945d   # list に表示される ID の先頭数文字で指定
```

一致するレコードが 1 件に定まらない場合はエラーになる。

## Web API

```bash
uv run fastapi dev    # 開発サーバー (自動リロード) を http://127.0.0.1:8000 で起動
```

`http://127.0.0.1:8000/docs` で Swagger UI から試せる。

| メソッド | パス | 内容 |
|---|---|---|
| `POST` | `/api/v1/entries` | 支出を追加 (201) |
| `GET` | `/api/v1/entries?month=YYYY-MM` | 一覧 (日付順) |
| `GET` | `/api/v1/entries/{id}` | 1 件取得 (なければ 404) |
| `DELETE` | `/api/v1/entries/{id}` | 削除 (204 / なければ 404) |
| `GET` | `/api/v1/entries/summary?month=YYYY-MM` | カテゴリ別集計 |

```bash
curl -X POST localhost:8000/api/v1/entries -H 'content-type: application/json' \
  -d '{"amount": 1200, "category": "food", "memo": "ランチ"}'
```

CLI と同じデータファイルを使う (`KAKEIBO_FILE` で変更可)。

## データファイル

デフォルトでは `~/.kakeibo/entries.json` に保存する。変更したい場合は `--file` オプションか環境変数 `KAKEIBO_FILE` で指定する。

```bash
uv run kakeibo --file /tmp/test.json list
KAKEIBO_FILE=/tmp/test.json uv run kakeibo list
```

## 開発

```bash
uv run pytest                 # テスト
uv run ruff check .           # lint
uv run ruff format .          # フォーマット
```

`uv run` を毎回付けたくない場合は `source .venv/bin/activate` してから `kakeibo ...` / `pytest` を直接実行できる。

## ディレクトリ構成

```
src/kakeibo/
├── models.py    # ドメインモデル (Entry / Category / Summary)。I/O はしない
├── storage.py   # 永続化 (Storage Protocol / JsonStorage)。CLI / API のことは知らない
├── cli.py       # Typer のコマンド定義と Rich での表示
└── api.py       # FastAPI のエンドポイント定義
tests/
├── conftest.py  # 共通フィクスチャ (storage / runner / client など)
└── test_*.py    # src/kakeibo/*.py と 1:1 対応
```

依存の向きは `cli / api → storage → models` の一方向。Phase 2 で `storage.py` を SQLModel に差し替えても `cli.py` / `api.py` は変更不要になるよう分けている。
