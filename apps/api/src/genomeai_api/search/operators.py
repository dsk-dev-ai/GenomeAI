from __future__ import annotations

import enum


class Operator(enum.StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    LIKE = "like"
    ILIKE = "ilike"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    CONTAINS = "contains"


COMPARISON_OPERATORS: frozenset[Operator] = frozenset({
    Operator.EQUALS,
    Operator.NOT_EQUALS,
    Operator.GREATER_THAN,
    Operator.GREATER_THAN_OR_EQUAL,
    Operator.LESS_THAN,
    Operator.LESS_THAN_OR_EQUAL,
})

RANGE_OPERATORS: frozenset[Operator] = frozenset({
    Operator.BETWEEN,
})

SET_OPERATORS: frozenset[Operator] = frozenset({
    Operator.IN,
    Operator.NOT_IN,
})

NULL_OPERATORS: frozenset[Operator] = frozenset({
    Operator.IS_NULL,
    Operator.IS_NOT_NULL,
})

STRING_OPERATORS: frozenset[Operator] = frozenset({
    Operator.LIKE,
    Operator.ILIKE,
    Operator.STARTS_WITH,
    Operator.ENDS_WITH,
    Operator.CONTAINS,
})

ALL_OPERATORS: frozenset[Operator] = frozenset({
    *COMPARISON_OPERATORS,
    *RANGE_OPERATORS,
    *SET_OPERATORS,
    *NULL_OPERATORS,
    *STRING_OPERATORS,
})

OPERATORS_REQUIRING_LIST: frozenset[Operator] = frozenset({
    Operator.BETWEEN,
    Operator.IN,
    Operator.NOT_IN,
})

OPERATORS_REQUIRING_NO_VALUE: frozenset[Operator] = frozenset({
    Operator.IS_NULL,
    Operator.IS_NOT_NULL,
})
