from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.expression import ColumnElement, column

_M = TypeVar("_M", bound=DeclarativeBase)


def apply_ts_rank(
    stmt: Select[tuple[_M]],
    vector: ColumnElement[Any],
    query: ColumnElement[Any],
    label: str = "rank",
    normalization: int = 0,
) -> Select[tuple[_M]]:
    rank_expr = func.ts_rank(vector, query, normalization).label(label)
    return stmt.add_columns(rank_expr)


def apply_ts_rank_cd(
    stmt: Select[tuple[_M]],
    vector: ColumnElement[Any],
    query: ColumnElement[Any],
    label: str = "rank",
    normalization: int = 0,
) -> Select[tuple[_M]]:
    rank_expr = func.ts_rank_cd(vector, query, normalization).label(label)
    return stmt.add_columns(rank_expr)


def order_by_rank_desc(
    stmt: Select[tuple[_M]],
    rank_label: str = "rank",
) -> Select[tuple[_M]]:
    return stmt.order_by(column(rank_label).desc())  # type: ignore[no-any-return]
