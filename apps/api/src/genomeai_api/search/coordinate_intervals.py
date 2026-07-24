from __future__ import annotations

from typing import TypeVar

from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.search.coordinate_types import CoordinateInterval, CoordinateMatchType

_M = TypeVar("_M", bound=DeclarativeBase)


def apply_coordinate_filter(
    stmt: Select[tuple[_M]],
    model: type[_M],
    interval: CoordinateInterval,
    match_type: CoordinateMatchType,
    chromosome_column: str = "chromosome",
    start_column: str = "start_position",
    end_column: str = "end_position",
) -> Select[tuple[_M]]:
    chrom_col = getattr(model, chromosome_column)
    start_col = getattr(model, start_column)
    end_col = getattr(model, end_column)

    q_chrom = interval.chromosome
    q_start = interval.start
    q_end = interval.end

    if match_type == CoordinateMatchType.EXACT:
        if start_column == end_column:
            return stmt.where(chrom_col == q_chrom, start_col == q_start)
        return stmt.where(chrom_col == q_chrom, start_col == q_start, end_col == q_end)

    if match_type == CoordinateMatchType.CONTAINS:
        if start_column == end_column:
            return stmt.where(chrom_col == q_chrom, start_col == q_start)
        return stmt.where(chrom_col == q_chrom, start_col <= q_start, end_col >= q_end)

    if match_type == CoordinateMatchType.CONTAINED_BY:
        if start_column == end_column:
            return stmt.where(chrom_col == q_chrom, start_col == q_start)
        return stmt.where(chrom_col == q_chrom, start_col >= q_start, end_col <= q_end)

    if match_type == CoordinateMatchType.OVERLAP:
        if start_column == end_column:
            return stmt.where(chrom_col == q_chrom, start_col == q_start)
        return stmt.where(chrom_col == q_chrom, start_col <= q_end, end_col >= q_start)

    if match_type == CoordinateMatchType.RANGE:
        if start_column == end_column:
            return stmt.where(chrom_col == q_chrom, start_col.between(q_start, q_end))
        return stmt.where(chrom_col == q_chrom, start_col >= q_start, end_col <= q_end)

    msg = f"Unsupported match type: {match_type}"
    raise ValueError(msg)
