from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select, func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.expression import ColumnElement

_M = TypeVar("_M", bound=DeclarativeBase)


def build_ts_headline(
    column: ColumnElement[Any],
    query: ColumnElement[Any],
    config: str | None = None,
    options: str | None = None,
) -> ColumnElement[Any]:
    args: list[Any] = []
    if config:
        args.append(config)
    args.append(column)
    args.append(query)
    if options:
        args.append(options)
    return func.ts_headline(*args)  # type: ignore[no-any-return]


def apply_ts_headlines(
    stmt: Select[tuple[_M]],
    model: type[_M],
    columns: list[str],
    query: ColumnElement[Any],
    config: str | None = None,
    options: str | None = None,
    label_suffix: str = "_highlight",
) -> Select[tuple[_M]]:
    for col_name in columns:
        col = getattr(model, col_name)
        headline = build_ts_headline(col, query, config=config, options=options)
        headline = headline.label(f"{col_name}{label_suffix}")  # type: ignore[attr-defined]
        stmt = stmt.add_columns(headline)
    return stmt
