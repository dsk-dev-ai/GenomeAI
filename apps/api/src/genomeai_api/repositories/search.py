from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from sqlalchemy import Select, func, inspect, select, types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.schemas.search import (
    AdvancedFilterGroup,
    CoordinateSearchRequest,
    FilterRule,
    SearchRequest,
    SortRequest,
)
from genomeai_api.search.autocomplete import build_prefix_query
from genomeai_api.search.coordinate_intervals import apply_coordinate_filter
from genomeai_api.search.coordinate_types import CoordinateInterval, CoordinateMatchType
from genomeai_api.search.expressions import (
    GroupExpression,
    LeafExpression,
)
from genomeai_api.search.fts import (
    QueryType,
    WeightType,
    build_tsquery,
    build_tsvector,
)
from genomeai_api.search.highlighting import apply_ts_headlines
from genomeai_api.search.operators import (
    Operator,
)
from genomeai_api.search.query import apply_fts_filter
from genomeai_api.search.query_builder import build_clause
from genomeai_api.search.ranking import apply_ts_rank, order_by_rank_desc
from genomeai_api.search.validation import (
    ValidationError,
    validate_expression,
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


def _is_text_column(model: type[M], field: str) -> bool:
    if not _is_mapped_column(model, field):
        return False
    column = getattr(model, field)
    return isinstance(column.type, types.String)


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


def _convert_to_expression(
    group: AdvancedFilterGroup,
) -> GroupExpression:
    children: list[LeafExpression | GroupExpression] = []
    for child in group.children:
        if isinstance(child, AdvancedFilterGroup):
            children.append(_convert_to_expression(child))
        else:
            try:
                operator = Operator(child.operator)
            except ValueError:
                msg = f"Invalid operator: {child.operator}"
                raise ValidationError(msg)
            children.append(
                LeafExpression(
                    field=child.field,
                    operator=operator,
                    value=child.value,
                )
            )
    return GroupExpression(
        connector=group.connector,
        children=tuple(children),
        negated=group.negated,
    )


def apply_advanced_filters(
    stmt: Select[tuple[M]],
    model: type[M],
    advanced_filters: AdvancedFilterGroup,
) -> Select[tuple[M]]:
    expr = _convert_to_expression(advanced_filters)
    validate_expression(model, expr)
    clause = build_clause(model, expr)
    return stmt.where(clause)


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

    if request.advanced_filters:
        stmt = apply_advanced_filters(stmt, model, request.advanced_filters)

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


@dataclass
class FTSResult(Generic[M]):
    items: list[M] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    ranks: list[float] | None = None
    highlights: list[list[tuple[str, str]]] | None = None

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


async def execute_fts_search(
    session: AsyncSession,
    model: type[M],
    request: SearchRequest,
    fts_columns: list[str],
    fts_query: str,
    fts_config: str = "english",
    query_type: QueryType = "plain",
    weights: list[WeightType] | None = None,
    highlight_columns: list[str] | None = None,
    base_stmt: Select[tuple[M]] | None = None,
) -> FTSResult[M]:
    for col in fts_columns:
        if not _is_text_column(model, col):
            msg = f"Invalid FTS column: {col}"
            raise ValueError(msg)

    if highlight_columns:
        for col in highlight_columns:
            if not _is_text_column(model, col):
                msg = f"Invalid highlight column: {col}"
                raise ValueError(msg)

    stmt: Select[tuple[M]] = base_stmt if base_stmt is not None else select(model)

    if request.filters:
        for rule in request.filters:
            _validate_filter_field(model, rule.field)
            _validate_filter_value(rule)
        stmt = apply_filters(stmt, model, request.filters)

    if request.advanced_filters:
        stmt = apply_advanced_filters(stmt, model, request.advanced_filters)

    column_elements = [getattr(model, col) for col in fts_columns]
    vector = build_tsvector(column_elements, weights=weights, config=fts_config)
    tsquery = build_tsquery(fts_query, query_type=query_type, config=fts_config)

    stmt = apply_fts_filter(stmt, vector, tsquery)

    rank_label = "_rank"
    stmt = apply_ts_rank(stmt, vector, tsquery, label=rank_label, normalization=0)

    if highlight_columns:
        stmt = apply_ts_headlines(
            stmt, model, highlight_columns, tsquery, config=fts_config,
        )

    if request.sort:
        _validate_sort_by(model, request.sort.sort_by)
        stmt = apply_sorting(stmt, model, request.sort)

    stmt = order_by_rank_desc(stmt, rank_label=rank_label)
    pk = _get_primary_key(model)
    if request.sort is None or request.sort.sort_by != pk:
        pk_column = getattr(model, pk)
        stmt = stmt.order_by(pk_column.asc())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count_result = await session.execute(count_stmt)
    total_count = total_count_result.scalar_one()

    stmt = apply_pagination(
        stmt,
        request.pagination.page,
        request.pagination.page_size,
    )

    result = await session.execute(stmt)
    rows = result.all()

    items = list[M]()
    ranks = list[float]()
    highlights: list[list[tuple[str, str]]] | None = (
        [] if highlight_columns else None
    )

    for row in rows:
        row_dict = row._mapping  # type: ignore[attr-defined]
        model_instance = row_dict.get(model.__tablename__, row[0])
        items.append(model_instance)
        ranks.append(float(row_dict.get(rank_label, 0.0)))

        if highlights is not None and highlight_columns:
            row_highlights: list[tuple[str, str]] = []
            for hc in highlight_columns:
                hl_key = f"{hc}_highlight"
                if hl_key in row_dict:
                    row_highlights.append((hc, str(row_dict[hl_key])))
            highlights.append(row_highlights)

    return FTSResult[M](
        items=items,
        total_count=total_count,
        page=request.pagination.page,
        page_size=request.pagination.page_size,
        ranks=ranks,
        highlights=highlights,
    )


async def execute_suggestions(
    session: AsyncSession,
    model: type[M],
    column_name: str,
    query: str,
    limit: int,
) -> list[str]:
    stmt = build_prefix_query(model, column_name, query, limit)
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]


async def execute_coordinate_search(
    session: AsyncSession,
    model: type[M],
    request: CoordinateSearchRequest,
    base_stmt: Select[tuple[M]] | None = None,
) -> SearchResult[M]:
    stmt: Select[tuple[M]] = base_stmt if base_stmt is not None else select(model)

    match_type = CoordinateMatchType(request.match_type)
    interval = CoordinateInterval(
        chromosome=request.interval.chromosome,
        start=request.interval.start,
        end=request.interval.end,
    )
    stmt = apply_coordinate_filter(
        stmt,
        model,
        interval,
        match_type,
        chromosome_column=request.chromosome_column,
        start_column=request.start_column,
        end_column=request.end_column,
    )

    if request.filters:
        for rule in request.filters:
            _validate_filter_field(model, rule.field)
            _validate_filter_value(rule)
        stmt = apply_filters(stmt, model, request.filters)

    if request.advanced_filters:
        stmt = apply_advanced_filters(stmt, model, request.advanced_filters)

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
