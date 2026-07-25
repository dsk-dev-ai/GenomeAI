from __future__ import annotations

from typing import Any, cast

from sqlalchemy.orm import DeclarativeBase

from genomeai_api.search.expressions import GroupExpression, LeafExpression
from genomeai_api.search.operators import (
    OPERATORS_REQUIRING_LIST,
    OPERATORS_REQUIRING_NO_VALUE,
    Operator,
)
from genomeai_api.search.validation import (
    MAX_EXPRESSIONS,
    MAX_RECURSION_DEPTH,
    ValidationError,
    validate_expression,
)

DSL_OP_MAP: dict[str, Operator] = {
    "eq": Operator.EQUALS,
    "ne": Operator.NOT_EQUALS,
    "gt": Operator.GREATER_THAN,
    "gte": Operator.GREATER_THAN_OR_EQUAL,
    "lt": Operator.LESS_THAN,
    "lte": Operator.LESS_THAN_OR_EQUAL,
    "between": Operator.BETWEEN,
    "in": Operator.IN,
    "not_in": Operator.NOT_IN,
    "is_null": Operator.IS_NULL,
    "is_not_null": Operator.IS_NOT_NULL,
    "like": Operator.LIKE,
    "ilike": Operator.ILIKE,
    "starts_with": Operator.STARTS_WITH,
    "ends_with": Operator.ENDS_WITH,
    "contains": Operator.CONTAINS,
}

SUPPORTED_DSL_OPS: frozenset[str] = frozenset(DSL_OP_MAP.keys())

LOGICAL_KEYS: frozenset[str] = frozenset({"and", "or", "not"})


def _validate_node_structure(node: object, depth: int) -> None:
    if not isinstance(node, dict):
        msg = f"Expected an object (dict) at depth {depth}, got {type(node).__name__}"
        raise ValidationError(msg)

    n: dict[str, Any] = node

    if not n:
        msg = f"Empty object at depth {depth}"
        raise ValidationError(msg)

    unknown_keys = set(n.keys()) - LOGICAL_KEYS - {"field", "op", "value"}
    if unknown_keys:
        msg = f"Unknown key(s) at depth {depth}: {', '.join(sorted(unknown_keys))}"
        raise ValidationError(msg)

    has_logical = bool(LOGICAL_KEYS & set(n.keys()))
    has_leaf = "field" in n or "op" in n or "value" in n

    if has_logical and has_leaf:
        msg = (
            f"Mixed logical keys and field/op/value at depth {depth}. "
            f"Use either a logical group (and/or/not) or a field condition, not both."
        )
        raise ValidationError(msg)

    if not has_logical and not has_leaf:
        msg = (
            f"Node at depth {depth} must contain either a logical key "
            f"(and/or/not) or field/op/value"
        )
        raise ValidationError(msg)

    if has_logical:
        node_keys = set(n.keys()) & LOGICAL_KEYS
        multiple_logical = len(node_keys) > 1

        if multiple_logical:
            msg = (
                f"Multiple logical keys at depth {depth}: {', '.join(sorted(node_keys))}. "
                f"Only one logical key allowed per node. "
                f"Nest 'not' explicitly, e.g. {{'not': {{'and': [...]}}}}."
            )
            raise ValidationError(msg)

        if "and" in n and not isinstance(n["and"], list):
            msg = f"'and' at depth {depth} must be a list"
            raise ValidationError(msg)
        if "or" in n and not isinstance(n["or"], list):
            msg = f"'or' at depth {depth} must be a list"
            raise ValidationError(msg)
        if "not" in n:
            if isinstance(n["not"], list):
                msg = f"'not' at depth {depth} must be a single object, not a list"
                raise ValidationError(msg)

    if has_leaf:
        if "field" not in n:
            msg = f"Leaf condition at depth {depth} is missing 'field'"
            raise ValidationError(msg)
        if "op" not in n:
            msg = f"Leaf condition at depth {depth} is missing 'op'"
            raise ValidationError(msg)

        op = n["op"]
        if op not in SUPPORTED_DSL_OPS:
            ops_list = ", ".join(sorted(SUPPORTED_DSL_OPS))
            msg = f"Unsupported operator '{op}' at depth {depth}. Supported: {ops_list}"
            raise ValidationError(msg)

        resolved = DSL_OP_MAP[op]
        value = n.get("value")

        if resolved in OPERATORS_REQUIRING_NO_VALUE:
            if value is not None:
                msg = f"Operator '{op}' at depth {depth} does not accept a value"
                raise ValidationError(msg)
        elif resolved in OPERATORS_REQUIRING_LIST:
            if not isinstance(value, list):
                msg = f"Operator '{op}' at depth {depth} requires a list value"
                raise ValidationError(msg)
            val_list: list[object] = value
            if resolved == Operator.BETWEEN and len(val_list) != 2:
                msg = f"Operator 'between' at depth {depth} requires exactly 2 values"
                raise ValidationError(msg)
            if resolved in (Operator.IN, Operator.NOT_IN) and len(val_list) == 0:
                msg = f"Operator '{op}' at depth {depth} requires a non-empty list"
                raise ValidationError(msg)
        else:
            if value is None:
                msg = f"Operator '{op}' at depth {depth} requires a non-null value"
                raise ValidationError(msg)


def _compile_node(
    node: object,
    model: type[DeclarativeBase],
    depth: int = 0,
    total_count: int = 0,
) -> tuple[LeafExpression | GroupExpression, int]:
    if depth > MAX_RECURSION_DEPTH:
        msg = f"Maximum recursion depth ({MAX_RECURSION_DEPTH}) exceeded"
        raise ValidationError(msg)

    _validate_node_structure(node, depth)
    assert isinstance(node, dict)
    n: dict[str, Any] = node

    total_count += 1
    if total_count > MAX_EXPRESSIONS:
        msg = f"Maximum expression count ({MAX_EXPRESSIONS}) exceeded"
        raise ValidationError(msg)

    has_logical = bool(LOGICAL_KEYS & set(n.keys()))

    if not has_logical:
        op_str = n["op"]
        operator = DSL_OP_MAP[op_str]
        expr = LeafExpression(
            field=n["field"],
            operator=operator,
            value=n.get("value"),
        )
        return expr, total_count

    children: list[LeafExpression | GroupExpression] = []
    connector: str = "AND"
    negated: bool = False

    if "and" in n:
        connector = "AND"
        for child_node in n["and"]:
            child_expr, total_count = _compile_node(child_node, model, depth + 1, total_count)
            children.append(child_expr)
    elif "or" in n:
        connector = "OR"
        for child_node in n["or"]:
            child_expr, total_count = _compile_node(child_node, model, depth + 1, total_count)
            children.append(child_expr)

    if "not" in n:
        inner = n["not"]
        inner_expr, total_count = _compile_node(inner, model, depth + 1, total_count)
        if isinstance(inner_expr, GroupExpression):
            inner_expr = GroupExpression(
                connector=inner_expr.connector,
                children=inner_expr.children,
                negated=not inner_expr.negated,
            )
        else:
            inner_expr = GroupExpression(
                connector="AND",
                children=(inner_expr,),
                negated=True,
            )
        return inner_expr, total_count

    if not children:
        msg = f"Group at depth {depth} must have at least one child"
        raise ValidationError(msg)

    expr = GroupExpression(
        connector=connector,
        children=tuple(children),
        negated=negated,
    )
    return expr, total_count


def compile_dsl(
    where: object,
    model: type[DeclarativeBase],
) -> GroupExpression:
    if not isinstance(where, dict):
        msg = f"DSL 'where' must be a dict, got {type(where).__name__}"
        raise ValidationError(msg)
    if not where:
        msg = "DSL 'where' must not be empty"
        raise ValidationError(msg)

    expr, _ = _compile_node(cast("dict[str, Any]", where), model)
    if not isinstance(expr, GroupExpression):
        expr = GroupExpression(children=(expr,))
    validate_expression(model, expr)
    return expr


# Exports for DSL operator mapping
__all__ = [
    "compile_dsl",
    "DSL_OP_MAP",
    "SUPPORTED_DSL_OPS",
]
