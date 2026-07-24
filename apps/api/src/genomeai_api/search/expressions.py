from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from genomeai_api.search.operators import Operator

Connector = Literal["AND", "OR"]


@dataclass(frozen=True)
class LeafExpression:
    field: str
    operator: Operator
    value: Any = None


@dataclass(frozen=True)
class GroupExpression:
    connector: Connector = "AND"
    children: tuple[LeafExpression | GroupExpression, ...] = field(default_factory=tuple)
    negated: bool = False


def count_expressions(expr: LeafExpression | GroupExpression) -> int:
    if isinstance(expr, LeafExpression):
        return 1
    total = 1
    for child in expr.children:
        total += count_expressions(child)
    return total


def max_depth(expr: LeafExpression | GroupExpression) -> int:
    if isinstance(expr, LeafExpression):
        return 1
    if not expr.children:
        return 1
    return 1 + max(max_depth(c) for c in expr.children)
