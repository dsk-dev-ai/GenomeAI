from __future__ import annotations

import re
from typing import TypeVar

from sqlalchemy import Select, inspect
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.search.coordinate_types import CoordinateInterval, CoordinateMatchType

_M = TypeVar("_M", bound=DeclarativeBase)

CHROMOSOME_PATTERN = re.compile(r"^(chr)?([1-9][0-9]?|X|Y|MT|M)$", re.IGNORECASE)


def _is_mapped_column(model: type[_M], field: str) -> bool:
    return field in _get_mapped_columns(model)


def _get_mapped_columns(model: type[_M]) -> frozenset[str]:
    mapper = inspect(model)
    return frozenset(mapper.column_attrs.keys())


def _validate_coordinate_columns(
    model: type[_M],
    chromosome_column: str,
    start_column: str,
    end_column: str,
) -> None:
    if not chromosome_column or not chromosome_column.strip():
        msg = "Chromosome column must be a non-empty string"
        raise ValueError(msg)
    if not start_column or not start_column.strip():
        msg = "Start column must be a non-empty string"
        raise ValueError(msg)
    if not end_column or not end_column.strip():
        msg = "End column must be a non-empty string"
        raise ValueError(msg)

    if not _is_mapped_column(model, chromosome_column):
        msg = (
            f"Invalid chromosome column: '{chromosome_column}' "
            f"— not a mapped column on {model.__name__}"
        )
        raise ValueError(msg)
    if not _is_mapped_column(model, start_column):
        msg = (
            f"Invalid start column: '{start_column}' "
            f"— not a mapped column on {model.__name__}"
        )
        raise ValueError(msg)
    if not _is_mapped_column(model, end_column):
        msg = (
            f"Invalid end column: '{end_column}' "
            f"— not a mapped column on {model.__name__}"
        )
        raise ValueError(msg)


def apply_coordinate_filter(
    stmt: Select[tuple[_M]],
    model: type[_M],
    interval: CoordinateInterval,
    match_type: CoordinateMatchType,
    chromosome_column: str = "chromosome",
    start_column: str = "start_position",
    end_column: str = "end_position",
) -> Select[tuple[_M]]:
    _validate_coordinate_columns(model, chromosome_column, start_column, end_column)

    chrom_col = getattr(model, chromosome_column)
    start_col = getattr(model, start_column)
    end_col = getattr(model, end_column)

    q_chrom = interval.chromosome
    q_start = interval.start
    q_end = interval.end

    is_point_model = start_column == end_column

    if match_type == CoordinateMatchType.EXACT:
        if is_point_model:
            # For point models (e.g. Variant), exact means position == query position
            return stmt.where(chrom_col == q_chrom, start_col == q_start)
        # For interval models, exact means both start and end match
        return stmt.where(chrom_col == q_chrom, start_col == q_start, end_col == q_end)

    if match_type == CoordinateMatchType.CONTAINS:
        if is_point_model:
            # Stored point is contained by query interval
            return stmt.where(chrom_col == q_chrom, start_col.between(q_start, q_end))
        # Stored interval contains query interval
        return stmt.where(chrom_col == q_chrom, start_col <= q_start, end_col >= q_end)

    if match_type == CoordinateMatchType.CONTAINED_BY:
        if is_point_model:
            # Stored point is within query interval
            return stmt.where(chrom_col == q_chrom, start_col.between(q_start, q_end))
        # Stored interval is within query interval
        return stmt.where(chrom_col == q_chrom, start_col >= q_start, end_col <= q_end)

    if match_type == CoordinateMatchType.OVERLAP:
        if is_point_model:
            # Stored point overlaps query interval if it falls within
            return stmt.where(chrom_col == q_chrom, start_col.between(q_start, q_end))
        # Intervals overlap
        return stmt.where(chrom_col == q_chrom, start_col <= q_end, end_col >= q_start)

    if match_type == CoordinateMatchType.RANGE:
        if is_point_model:
            # Point falls within range
            return stmt.where(chrom_col == q_chrom, start_col.between(q_start, q_end))
        # Interval within range
        return stmt.where(chrom_col == q_chrom, start_col >= q_start, end_col <= q_end)

    msg = f"Unsupported match type: {match_type}"
    raise ValueError(msg)
