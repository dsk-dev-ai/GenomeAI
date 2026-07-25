from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CoordinateMatchType(StrEnum):
    EXACT = "exact"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    OVERLAP = "overlap"
    RANGE = "range"


@dataclass(frozen=True)
class CoordinateInterval:
    chromosome: str
    start: int
    end: int
