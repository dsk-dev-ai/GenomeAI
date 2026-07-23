from __future__ import annotations

from typing import Any, Literal

from sqlalchemy import func
from sqlalchemy.sql.expression import ColumnElement

QueryType = Literal["plain", "phrase", "websearch", "raw"]
WeightType = Literal["A", "B", "C", "D"]
TSConfig = str

_VALID_WEIGHTS: frozenset[str] = frozenset({"A", "B", "C", "D"})


def build_tsvector(
    columns: list[ColumnElement[Any]],
    weights: list[WeightType] | None = None,
    config: TSConfig | None = None,
) -> ColumnElement[Any]:
    if not columns:
        msg = "At least one column is required to build a tsvector"
        raise ValueError(msg)

    if weights is not None:
        if len(weights) != len(columns):
            msg = (
                f"Number of weights ({len(weights)}) must match"
                f" number of columns ({len(columns)})"
            )
            raise ValueError(msg)
        for w in weights:
            if w not in _VALID_WEIGHTS:
                msg = f"Invalid weight '{w}'; must be one of {sorted(_VALID_WEIGHTS)}"
                raise ValueError(msg)

    weighted_parts: list[ColumnElement[Any]] = []
    for i, col in enumerate(columns):
        safe_col = func.coalesce(col, "")
        args: list[Any] = []
        if config:
            args.append(config)
        args.append(safe_col)
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
