from __future__ import annotations

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.search.expressions import (
    GroupExpression,
    LeafExpression,
    count_expressions,
    max_depth,
)
from genomeai_api.search.operators import (
    OPERATORS_REQUIRING_LIST,
    OPERATORS_REQUIRING_NO_VALUE,
    Operator,
)

MAX_RECURSION_DEPTH = 10
MAX_EXPRESSIONS = 200


class ValidationError(ValueError):
    pass


def validate_field_name(model: type[DeclarativeBase], field: str) -> None:
    mapper = inspect(model)
    if field not in mapper.column_attrs:
        msg = f"Invalid filter field: '{field}' — not a mapped column on {model.__name__}"
        raise ValidationError(msg)


def validate_operator_value(operator: Operator, value: Any) -> None:
    if operator in OPERATORS_REQUIRING_NO_VALUE:
        return

    if operator in OPERATORS_REQUIRING_LIST:
        if not isinstance(value, list):
            msg = f"Operator '{operator.value}' requires a list value, got {type(value).__name__}"
            raise ValidationError(msg)
        vl: list[Any] = value
        if operator == Operator.BETWEEN and len(vl) != 2:
            msg = f"Operator 'between' requires exactly 2 values, got {len(vl)}"
            raise ValidationError(msg)
        if operator in (Operator.IN, Operator.NOT_IN) and len(vl) == 0:
            msg = f"Operator '{operator.value}' requires a non-empty list"
            raise ValidationError(msg)
        return

    if value is None:
        msg = f"Operator '{operator.value}' requires a non-null value"
        raise ValidationError(msg)


def validate_leaf(model: type[DeclarativeBase], expr: LeafExpression) -> None:
    validate_field_name(model, expr.field)
    validate_operator_value(expr.operator, expr.value)


def validate_group(
    model: type[DeclarativeBase],
    expr: GroupExpression,
    depth: int = 0,
    total: int = 0,
) -> None:
    if depth > MAX_RECURSION_DEPTH:
        msg = f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded"
        raise ValidationError(msg)

    total += 1
    if total > MAX_EXPRESSIONS:
        msg = f"Maximum expression count ({MAX_EXPRESSIONS}) exceeded"
        raise ValidationError(msg)

    if expr.connector not in ("AND", "OR"):
        msg = f"Invalid connector: '{expr.connector}' — must be 'AND' or 'OR'"
        raise ValidationError(msg)

    if not expr.children:
        msg = "Group expression must have at least one child"
        raise ValidationError(msg)

    for child in expr.children:
        if isinstance(child, LeafExpression):
            total += 1
            if total > MAX_EXPRESSIONS:
                msg = f"Maximum expression count ({MAX_EXPRESSIONS}) exceeded"
                raise ValidationError(msg)
            validate_leaf(model, child)
        else:
            validate_group(model, child, depth=depth + 1, total=total)


def validate_expression(
    model: type[DeclarativeBase],
    expr: LeafExpression | GroupExpression,
) -> None:
    if isinstance(expr, LeafExpression):
        validate_leaf(model, expr)
    else:
        validate_group(model, expr)

    actual_depth = max_depth(expr)
    if actual_depth > MAX_RECURSION_DEPTH:
        msg = f"Expression depth ({actual_depth}) exceeds maximum ({MAX_RECURSION_DEPTH})"
        raise ValidationError(msg)

    actual_count = count_expressions(expr)
    if actual_count > MAX_EXPRESSIONS:
        msg = f"Expression count ({actual_count}) exceeds maximum ({MAX_EXPRESSIONS})"
        raise ValidationError(msg)
