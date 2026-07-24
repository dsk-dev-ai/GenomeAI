from __future__ import annotations

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.elements import ColumnElement

from genomeai_api.search.expressions import GroupExpression, LeafExpression
from genomeai_api.search.operators import Operator


def _build_leaf_clause(
    model: type[DeclarativeBase],
    expr: LeafExpression,
) -> ColumnElement[bool]:
    column = getattr(model, expr.field)

    if expr.operator == Operator.EQUALS:
        return column == expr.value
    if expr.operator == Operator.NOT_EQUALS:
        return column != expr.value
    if expr.operator == Operator.GREATER_THAN:
        return column > expr.value
    if expr.operator == Operator.GREATER_THAN_OR_EQUAL:
        return column >= expr.value
    if expr.operator == Operator.LESS_THAN:
        return column < expr.value
    if expr.operator == Operator.LESS_THAN_OR_EQUAL:
        return column <= expr.value
    if expr.operator == Operator.BETWEEN:
        return column.between(expr.value[0], expr.value[1])
    if expr.operator == Operator.IN:
        return column.in_(expr.value)
    if expr.operator == Operator.NOT_IN:
        return column.notin_(expr.value)
    if expr.operator == Operator.IS_NULL:
        return column.is_(None)
    if expr.operator == Operator.IS_NOT_NULL:
        return column.isnot(None)
    if expr.operator == Operator.LIKE:
        return column.like(expr.value)
    if expr.operator == Operator.ILIKE:
        return column.ilike(expr.value)
    if expr.operator == Operator.STARTS_WITH:
        return column.startswith(expr.value)
    if expr.operator == Operator.ENDS_WITH:
        return column.endswith(expr.value)
    if expr.operator == Operator.CONTAINS:
        return column.contains(expr.value)

    msg = f"Unknown operator: {expr.operator}"
    raise ValueError(msg)


def build_clause(
    model: type[DeclarativeBase],
    expr: LeafExpression | GroupExpression,
) -> ColumnElement[bool]:
    if isinstance(expr, LeafExpression):
        return _build_leaf_clause(model, expr)

    child_clauses: list[ColumnElement[bool]] = [
        build_clause(model, child) for child in expr.children
    ]

    if expr.connector == "AND":
        combined = and_(*child_clauses)
    else:
        combined = or_(*child_clauses)

    if expr.negated:
        return not_(combined)
    return combined
