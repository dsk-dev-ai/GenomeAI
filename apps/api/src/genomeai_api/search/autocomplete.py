from __future__ import annotations

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import DeclarativeBase


def build_prefix_query(
    model: type[DeclarativeBase],
    column_name: str,
    query: str,
    limit: int,
) -> Select[tuple[str]]:
    column = getattr(model, column_name)
    query_lower = query.lower()
    like_pattern = f"{query_lower}%"

    exact_case = case(
        (func.lower(column) == query_lower, 0),
        else_=1,
    )

    stmt: Select[tuple[str]] = (
        select(column)
        .where(func.lower(column).like(like_pattern))
        .distinct()
        .order_by(exact_case, column.asc())
        .limit(limit)
    )
    return stmt
