from __future__ import annotations

import re

from genomeai_api.search.coordinate_types import CoordinateMatchType

CHROMOSOME_PATTERN = re.compile(r"^(chr)?([1-9][0-9]?|X|Y|MT|M)$", re.IGNORECASE)

SUPPORTED_COORDINATE_MATCH_TYPES: frozenset[str] = frozenset(
    t.value for t in CoordinateMatchType
)


def validate_chromosome(chromosome: str) -> None:
    if not chromosome or not chromosome.strip():
        msg = "Chromosome must be a non-empty string"
        raise ValueError(msg)
    if not CHROMOSOME_PATTERN.match(chromosome):
        msg = f"Invalid chromosome format: '{chromosome}'"
        raise ValueError(msg)


def validate_coordinate(value: int, name: str = "coordinate") -> None:
    if type(value) is not int:
        msg = f"{name} must be an integer, got {type(value).__name__}"
        raise ValueError(msg)
    if value < 0:
        msg = f"{name} must be non-negative, got {value}"
        raise ValueError(msg)


def validate_interval(start: int, end: int) -> None:
    if start > end:
        msg = f"Start coordinate ({start}) must not exceed end coordinate ({end})"
        raise ValueError(msg)


def validate_match_type(match_type: str) -> None:
    if match_type not in SUPPORTED_COORDINATE_MATCH_TYPES:
        types_list = ", ".join(sorted(SUPPORTED_COORDINATE_MATCH_TYPES))
        msg = f"Unsupported match type: '{match_type}'. Supported types: {types_list}"
        raise ValueError(msg)


def validate_coordinate_request(
    chromosome: str,
    start: int,
    end: int,
    match_type: str,
) -> None:
    validate_chromosome(chromosome)
    validate_coordinate(start, "start")
    validate_coordinate(end, "end")
    validate_interval(start, end)
    validate_match_type(match_type)
