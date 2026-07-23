from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Computed, Index
from sqlalchemy.dialects.postgresql import TSVECTOR


def create_gin_index(
    name: str,
    table_name: str,
    column_name: str,
) -> Index:
    return Index(
        name,
        Column(column_name),  # type: ignore[arg-type]
        postgresql_using="gin",
    )


def create_tsvector_index(
    name: str,
    table_name: str,
    vector_column_name: str,
) -> Index:
    return Index(
        name,
        Column(vector_column_name),  # type: ignore[arg-type]
        postgresql_using="gin",
    )


def create_tsvector_column(
    column_name: str,
    tsvector_expr: str,
) -> Column[Any]:
    return Column(
        column_name,
        TSVECTOR,
        Computed(tsvector_expr, persisted=True),
    )
