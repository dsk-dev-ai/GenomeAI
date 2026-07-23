from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from sqlalchemy import Select, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.schemas.search import (
    FilterRule,
    SearchRequest,
    SortRequest,
)

M = TypeVar("M", bound=DeclarativeBase)


@dataclass
class SearchResult(Generic[M]):
    items: list[M] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return max(1, -(-self.total_count // self.page_size))

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


def _get_mapped_columns(model: type[M]) -> frozenset[str]:
    mapper = inspect(model)
    return frozenset(mapper.column_attrs.keys())


def _get_primary_key(model: type[M]) -> str:
    mapper = inspect(model)
    pk = mapper.primary_key[0]
    assert pk is not None
    return str(pk.key)


def _is_mapped_column(model: type[M], field: str) -> bool:
    return field in _get_mapped_columns(model)


def apply_pagination(
    stmt: Select[tuple[M]], page: int, page_size: int
) -> Select[tuple[M]]:
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    return stmt


def apply_sorting(
    stmt: Select[tuple[M]], model: type[M], sort: SortRequest
) -> Select[tuple[M]]:
    if not _is_mapped_column(model, sort.sort_by):
        msg = f"Invalid sort field: {sort.sort_by}"
        raise ValueError(msg)
    column = getattr(model, sort.sort_by)
    order = column.asc() if sort.sort_order == "asc" else column.desc()
    stmt = stmt.order_by(order)
    return stmt


def apply_filter(
    stmt: Select[tuple[M]], model: type[M], rule: FilterRule
) -> Select[tuple[M]]:
    if not _is_mapped_column(model, rule.field):
        msg = f"Invalid filter field: {rule.field}"
        raise ValueError(msg)
    column = getattr(model, rule.field)

    if rule.operator == "equals":
        return stmt.where(column == rule.value)
    if rule.operator == "contains":
        return stmt.where(column.contains(rule.value))
    if rule.operator == "starts_with":
        return stmt.where(column.startswith(rule.value))
    if rule.operator == "ends_with":
        return stmt.where(column.endswith(rule.value))
    if rule.operator == "in":
        if not isinstance(rule.value, list):
            msg = "Filter value for 'in' operator must be a list"
            raise TypeError(msg)
        return stmt.where(column.in_(rule.value))
    if rule.operator == "is_null":
        if rule.value:
            return stmt.where(column.is_(None))
        return stmt.where(column.isnot(None))

    msg = f"Unknown filter operator: {rule.operator}"
    raise ValueError(msg)


def apply_filters(
    stmt: Select[tuple[M]], model: type[M], filters: list[FilterRule]
) -> Select[tuple[M]]:
    for rule in filters:
        stmt = apply_filter(stmt, model, rule)
    return stmt


def _validate_sort_by(
    model: type[M], sort_by: str
) -> None:
    if not _is_mapped_column(model, sort_by):
        msg = f"Invalid sort field: {sort_by}"
        raise ValueError(msg)


def _validate_filter_field(
    model: type[M], field: str
) -> None:
    if not _is_mapped_column(model, field):
        msg = f"Invalid filter field: {field}"
        raise ValueError(msg)


def _validate_filter_value(
    rule: FilterRule,
) -> None:
    if rule.operator == "in" and not isinstance(rule.value, list):
        msg = "Filter value for 'in' operator must be a list"
        raise TypeError(msg)


def _ensure_deterministic_ordering(
    stmt: Select[tuple[M]], model: type[M], sort: SortRequest | None
) -> Select[tuple[M]]:
    pk = _get_primary_key(model)
    pk_column = getattr(model, pk)

    if sort is None:
        return stmt.order_by(pk_column.asc())

    if sort.sort_by != pk:
        stmt = stmt.order_by(pk_column.asc())

    return stmt


async def execute_search(
    session: AsyncSession,
    model: type[M],
    request: SearchRequest,
    base_stmt: Select[tuple[M]] | None = None,
) -> SearchResult[M]:
    stmt: Select[tuple[M]] = base_stmt if base_stmt is not None else select(model)

    if request.filters:
        for rule in request.filters:
            _validate_filter_field(model, rule.field)
            _validate_filter_value(rule)
        stmt = apply_filters(stmt, model, request.filters)

    if request.sort:
        _validate_sort_by(model, request.sort.sort_by)
        stmt = apply_sorting(stmt, model, request.sort)

    stmt = _ensure_deterministic_ordering(stmt, model, request.sort)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count_result = await session.execute(count_stmt)
    total_count = total_count_result.scalar_one()

    stmt = apply_pagination(
        stmt,
        request.pagination.page,
        request.pagination.page_size,
    )

    result = await session.execute(stmt)
    items: list[M] = list(result.scalars().all())

    return SearchResult[M](
        items=items,
        total_count=total_count,
        page=request.pagination.page,
        page_size=request.pagination.page_size,
    )
