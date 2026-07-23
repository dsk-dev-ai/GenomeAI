from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.expression import ColumnElement

from genomeai_api.search.fts import (
    QueryType,
    TSConfig,
    WeightType,
    build_tsquery,
    build_tsvector,
)

_M = TypeVar("_M", bound=DeclarativeBase)


def apply_fts_filter(
    stmt: Select[tuple[_M]],
    vector: ColumnElement[Any],
    query: ColumnElement[Any],
) -> Select[tuple[_M]]:
    return stmt.where(vector.op("@@")(query))


def apply_fts_to_statement(
    stmt: Select[tuple[_M]],
    model: type[_M],
    columns: list[str],
    search_query: str,
    query_type: QueryType = "plain",
    config: TSConfig | None = None,
    weights: list[WeightType] | None = None,
) -> Select[tuple[_M]]:
    column_elements = [getattr(model, col) for col in columns]
    vector = build_tsvector(column_elements, weights=weights, config=config)
    tsquery = build_tsquery(search_query, query_type=query_type, config=config)
    return apply_fts_filter(stmt, vector, tsquery)
