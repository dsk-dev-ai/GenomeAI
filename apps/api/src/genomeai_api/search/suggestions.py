from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SuggestionMatchType(StrEnum):
    EXACT = "exact"
    PREFIX = "prefix"
    ALPHABETICAL = "alphabetical"


@dataclass(frozen=True)
class Suggestion:
    domain: str
    field: str
    value: str
    rank: int
    match_type: SuggestionMatchType


def rank_suggestions(
    values: list[str],
    query: str,
    domain: str,
    field: str,
) -> list[Suggestion]:
    query_lower = query.lower()
    scored: list[Suggestion] = []
    seen: set[str] = set()

    for rank, value in enumerate(values):
        if value in seen:
            continue
        seen.add(value)
        value_lower = value.lower()
        if value_lower == query_lower:
            match_type = SuggestionMatchType.EXACT
        elif value_lower.startswith(query_lower):
            match_type = SuggestionMatchType.PREFIX
        else:
            match_type = SuggestionMatchType.ALPHABETICAL
        scored.append(
            Suggestion(
                domain=domain,
                field=field,
                value=value,
                rank=rank,
                match_type=match_type,
            )
        )

    scored.sort(key=_suggestion_sort_key)
    for i, s in enumerate(scored):
        scored[i] = Suggestion(
            domain=s.domain,
            field=s.field,
            value=s.value,
            rank=i,
            match_type=s.match_type,
        )
    return scored


def _suggestion_sort_key(s: Suggestion) -> tuple[int, str]:
    order = {
        SuggestionMatchType.EXACT: 0,
        SuggestionMatchType.PREFIX: 1,
        SuggestionMatchType.ALPHABETICAL: 2,
    }
    return (order[s.match_type], s.value.lower())
