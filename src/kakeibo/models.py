"""ドメインモデル。"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Category(StrEnum):
    """支出カテゴリ。"""

    FOOD = "food"
    HOUSING = "housing"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    OTHER = "other"


class Entry(BaseModel):
    """家計簿の 1 レコード。"""

    id: UUID = Field(default_factory=uuid4)
    amount: int = Field(gt=0, description="金額 (円)。正の整数のみ")
    category: Category
    memo: str = ""
    # フィールド名 date が型名 date を隠して Pydantic が型を解決できなくなるため、
    # datetime モジュールは dt として import している
    date: dt.date = Field(default_factory=dt.date.today)


class Summary(BaseModel):
    """集計結果。カテゴリごとの合計と総額。"""

    total: int
    by_category: dict[Category, int]

    @classmethod
    def from_entries(cls, entries: list[Entry]) -> Summary:
        by_category: dict[Category, int] = {}
        for e in entries:
            by_category[e.category] = by_category.get(e.category, 0) + e.amount
        return cls(total=sum(by_category.values()), by_category=by_category)
