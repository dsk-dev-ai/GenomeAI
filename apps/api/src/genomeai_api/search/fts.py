from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import func
from sqlalchemy.sql.expression import ColumnElement

QueryType = Literal["plain", "phrase", "websearch", "raw"]
TSConfig = str


def build_tsvector(
    columns: list[ColumnElement[Any]],
    weights: list[str] | None = None,
    config: TSConfig | None = None,
) -> ColumnElement[Any]:
    if not columns:
        msg = "At least one column is required to build a tsvector"
        raise ValueError(msg)

    if weights and len(weights) != len(columns):
        msg = "Number of weights must match number of columns"
        raise ValueError(msg)

    weighted_parts: list[ColumnElement[Any]] = []
    for i, col in enumerate(columns):
        args: list[Any] = []
        if config:
            args.append(config)
        args.append(col)
        tsvector = func.to_tsvector(*args)
        if weights:
            tsvector = func.setweight(tsvector, weights[i])
        weighted_parts.append(tsvector)

    vector: ColumnElement[Any] = weighted_parts[0]
    for part in weighted_parts[1:]:
        vector = vector.op("||")(part)

    return vector


def build_tsquery(
    query: str,
    query_type: QueryType = "plain",
    config: TSConfig | None = None,
) -> ColumnElement[Any]:
    if not query.strip():
        msg = "Search query must not be empty"
        raise ValueError(msg)

    args: list[Any] = []
    if config:
        args.append(config)
    args.append(query)

    if query_type == "plain":
        return func.plainto_tsquery(*args)  # type: ignore[no-any-return]
    if query_type == "phrase":
        return func.phraseto_tsquery(*args)  # type: ignore[no-any-return]
    if query_type == "websearch":
        return func.websearch_to_tsquery(*args)  # type: ignore[no-any-return]
    if query_type == "raw":
        return func.to_tsquery(*args)  # type: ignore[no-any-return]

    msg = f"Unknown query type: {query_type}"
    raise ValueError(msg)
