from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.repositories.search import (
    _convert_to_expression,
    apply_advanced_filters,
    execute_search,
)
from genomeai_api.schemas.search import (
    AdvancedFilterGroup,
    AdvancedFilterRule,
    FilterRule,
    PaginationRequest,
    SearchRequest,
    SortRequest,
)
from genomeai_api.search.expressions import (
    GroupExpression,
    LeafExpression,
    count_expressions,
    max_depth,
)
from genomeai_api.search.operators import (
    ALL_OPERATORS,
    COMPARISON_OPERATORS,
    NULL_OPERATORS,
    OPERATORS_REQUIRING_LIST,
    OPERATORS_REQUIRING_NO_VALUE,
    RANGE_OPERATORS,
    SET_OPERATORS,
    STRING_OPERATORS,
    Operator,
)
from genomeai_api.search.query_builder import build_clause
from genomeai_api.search.validation import (
    MAX_EXPRESSIONS,
    MAX_RECURSION_DEPTH,
    ValidationError,
    validate_expression,
    validate_field_name,
    validate_operator_value,
)
from sqlalchemy import select

# ---------------------------------------------------------------------------
# Operator definitions
# ---------------------------------------------------------------------------


class TestOperatorEnum:
    def test_all_operators_defined(self) -> None:
        expected = {
            "equals",
            "not_equals",
            "greater_than",
            "greater_than_or_equal",
            "less_than",
            "less_than_or_equal",
            "between",
            "in",
            "not_in",
            "is_null",
            "is_not_null",
            "like",
            "ilike",
            "starts_with",
            "ends_with",
            "contains",
        }
        actual = {op.value for op in Operator}
        assert actual == expected

    def test_comparison_operators(self) -> None:
        assert Operator.EQUALS in COMPARISON_OPERATORS
        assert Operator.NOT_EQUALS in COMPARISON_OPERATORS
        assert Operator.GREATER_THAN in COMPARISON_OPERATORS
        assert Operator.GREATER_THAN_OR_EQUAL in COMPARISON_OPERATORS
        assert Operator.LESS_THAN in COMPARISON_OPERATORS
        assert Operator.LESS_THAN_OR_EQUAL in COMPARISON_OPERATORS
        assert len(COMPARISON_OPERATORS) == 6

    def test_range_operators(self) -> None:
        assert Operator.BETWEEN in RANGE_OPERATORS
        assert len(RANGE_OPERATORS) == 1

    def test_set_operators(self) -> None:
        assert Operator.IN in SET_OPERATORS
        assert Operator.NOT_IN in SET_OPERATORS
        assert len(SET_OPERATORS) == 2

    def test_null_operators(self) -> None:
        assert Operator.IS_NULL in NULL_OPERATORS
        assert Operator.IS_NOT_NULL in NULL_OPERATORS
        assert len(NULL_OPERATORS) == 2

    def test_string_operators(self) -> None:
        assert Operator.LIKE in STRING_OPERATORS
        assert Operator.ILIKE in STRING_OPERATORS
        assert Operator.STARTS_WITH in STRING_OPERATORS
        assert Operator.ENDS_WITH in STRING_OPERATORS
        assert Operator.CONTAINS in STRING_OPERATORS
        assert len(STRING_OPERATORS) == 5

    def test_operators_requiring_list(self) -> None:
        assert Operator.BETWEEN in OPERATORS_REQUIRING_LIST
        assert Operator.IN in OPERATORS_REQUIRING_LIST
        assert Operator.NOT_IN in OPERATORS_REQUIRING_LIST
        assert len(OPERATORS_REQUIRING_LIST) == 3

    def test_operators_requiring_no_value(self) -> None:
        assert Operator.IS_NULL in OPERATORS_REQUIRING_NO_VALUE
        assert Operator.IS_NOT_NULL in OPERATORS_REQUIRING_NO_VALUE
        assert len(OPERATORS_REQUIRING_NO_VALUE) == 2

    def test_all_operators_union(self) -> None:
        union = (
            COMPARISON_OPERATORS
            | RANGE_OPERATORS
            | SET_OPERATORS
            | NULL_OPERATORS
            | STRING_OPERATORS
        )
        assert union == ALL_OPERATORS
        assert len(ALL_OPERATORS) == 16


# ---------------------------------------------------------------------------
# Expression tree
# ---------------------------------------------------------------------------


class TestExpressions:
    def test_leaf_expression(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.EQUALS, value="test")
        assert expr.field == "study_name"
        assert expr.operator == Operator.EQUALS
        assert expr.value == "test"

    def test_and_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="active"),
            ),
        )
        assert expr.connector == "AND"
        assert not expr.negated
        assert len(expr.children) == 2

    def test_or_group(self) -> None:
        expr = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="y"),
            ),
        )
        assert expr.connector == "OR"
        assert len(expr.children) == 2

    def test_negated_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(LeafExpression(field="status", operator=Operator.EQUALS, value="closed"),),
            negated=True,
        )
        assert expr.negated

    def test_nested_groups(self) -> None:
        inner = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="status", operator=Operator.EQUALS, value="a"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="b"),
            ),
        )
        outer = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="test"),
                inner,
            ),
        )
        assert len(outer.children) == 2
        assert isinstance(outer.children[1], GroupExpression)

    def test_leaf_immutable(self) -> None:
        expr = LeafExpression(field="x", operator=Operator.EQUALS, value=1)
        with pytest.raises(AttributeError):
            expr.field = "y"  # type: ignore[misc]

    def test_count_expressions(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="a", operator=Operator.EQUALS, value=1),
                LeafExpression(field="b", operator=Operator.EQUALS, value=2),
                GroupExpression(
                    connector="OR",
                    children=(
                        LeafExpression(field="c", operator=Operator.EQUALS, value=3),
                        LeafExpression(field="d", operator=Operator.EQUALS, value=4),
                    ),
                ),
            ),
        )
        assert count_expressions(expr) == 6  # 1 outer + 2 leaves + 1 inner + 2 inner leaves

    def test_max_depth(self) -> None:
        inner = GroupExpression(
            connector="OR",
            children=(LeafExpression(field="x", operator=Operator.EQUALS, value=1),),
        )
        middle = GroupExpression(
            connector="AND",
            children=(inner, LeafExpression(field="y", operator=Operator.EQUALS, value=2)),
        )
        outer = GroupExpression(
            connector="AND",
            children=(middle, LeafExpression(field="z", operator=Operator.EQUALS, value=3)),
        )
        assert max_depth(outer) == 4


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidateFieldName:
    def test_valid_field(self) -> None:
        validate_field_name(Study, "study_name")

    def test_valid_field_with_id(self) -> None:
        validate_field_name(Study, "study_id")

    def test_invalid_field_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid filter field: 'nonexistent'"):
            validate_field_name(Study, "nonexistent")

    def test_metadata_field_raises(self) -> None:
        with pytest.raises(ValidationError, match="metadata"):
            validate_field_name(Study, "metadata")


class TestValidateOperatorValue:
    def test_comparison_requires_non_null(self) -> None:
        with pytest.raises(ValidationError, match="requires a non-null value"):
            validate_operator_value(Operator.EQUALS, None)

    def test_between_requires_list(self) -> None:
        with pytest.raises(ValidationError, match="requires a list"):
            validate_operator_value(Operator.BETWEEN, "not-a-list")

    def test_between_requires_exactly_two(self) -> None:
        with pytest.raises(ValidationError, match="requires exactly 2"):
            validate_operator_value(Operator.BETWEEN, [1])

    def test_between_accepts_two_values(self) -> None:
        validate_operator_value(Operator.BETWEEN, [1, 10])

    def test_in_requires_list(self) -> None:
        with pytest.raises(ValidationError, match="requires a list"):
            validate_operator_value(Operator.IN, "not-a-list")

    def test_in_requires_non_empty(self) -> None:
        with pytest.raises(ValidationError, match="requires a non-empty list"):
            validate_operator_value(Operator.IN, [])

    def test_in_accepts_list(self) -> None:
        validate_operator_value(Operator.IN, ["a", "b"])

    def test_not_in_requires_list(self) -> None:
        with pytest.raises(ValidationError, match="requires a list"):
            validate_operator_value(Operator.NOT_IN, "not-a-list")

    def test_not_in_requires_non_empty(self) -> None:
        with pytest.raises(ValidationError, match="requires a non-empty list"):
            validate_operator_value(Operator.NOT_IN, [])

    def test_is_null_accepts_any(self) -> None:
        validate_operator_value(Operator.IS_NULL, None)
        validate_operator_value(Operator.IS_NULL, True)
        validate_operator_value(Operator.IS_NULL, "whatever")

    def test_is_not_null_accepts_any(self) -> None:
        validate_operator_value(Operator.IS_NOT_NULL, None)

    def test_string_operator_requires_non_null(self) -> None:
        with pytest.raises(ValidationError, match="requires a non-null value"):
            validate_operator_value(Operator.LIKE, None)
        with pytest.raises(ValidationError, match="requires a non-null value"):
            validate_operator_value(Operator.CONTAINS, None)


class TestValidateLeaf:
    def test_valid_leaf(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.EQUALS, value="test")
        validate_expression(Study, expr)

    def test_invalid_field_raises(self) -> None:
        expr = LeafExpression(field="nonexistent", operator=Operator.EQUALS, value="x")
        with pytest.raises(ValidationError, match="nonexistent"):
            validate_expression(Study, expr)

    def test_null_value_for_comparison_raises(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.EQUALS, value=None)
        with pytest.raises(ValidationError, match="requires a non-null value"):
            validate_expression(Study, expr)

    def test_invalid_list_for_between_raises(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.BETWEEN, value="x")
        with pytest.raises(ValidationError, match="requires a list"):
            validate_expression(Study, expr)


class TestValidateGroup:
    def test_empty_group_raises(self) -> None:
        expr = GroupExpression(connector="AND", children=())
        with pytest.raises(ValidationError, match="at least one child"):
            validate_expression(Study, expr)

    def test_invalid_connector_raises(self) -> None:
        bad = GroupExpression(
            connector="XOR",  # type: ignore[arg-type]
            children=(LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),),
        )
        with pytest.raises(ValidationError, match="Invalid connector"):
            validate_expression(Study, bad)

    def test_valid_and_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="y"),
            ),
        )
        validate_expression(Study, expr)

    def test_valid_or_group(self) -> None:
        expr = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="y"),
            ),
        )
        validate_expression(Study, expr)

    def test_negated_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(LeafExpression(field="status", operator=Operator.EQUALS, value="closed"),),
            negated=True,
        )
        validate_expression(Study, expr)

    def test_nested_group(self) -> None:
        inner = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="status", operator=Operator.EQUALS, value="a"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="b"),
            ),
        )
        outer = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="test"),
                inner,
            ),
        )
        validate_expression(Study, outer)


class TestValidateRecursionDepth:
    def test_exceeds_max_depth(self) -> None:
        deep = LeafExpression(field="study_name", operator=Operator.EQUALS, value="x")
        limit = MAX_RECURSION_DEPTH + 2
        for _ in range(limit):
            deep = GroupExpression(connector="AND", children=(deep,))
        with pytest.raises(ValidationError, match="recursion depth|exceeded"):
            validate_expression(Study, deep)

    def test_at_max_depth(self) -> None:
        deep = LeafExpression(field="study_name", operator=Operator.EQUALS, value="x")
        for _ in range(MAX_RECURSION_DEPTH - 1):
            deep = GroupExpression(connector="AND", children=(deep,))
        validate_expression(Study, deep)


class TestValidateExpressionCount:
    def test_exceeds_max_count(self) -> None:
        leaves = tuple(
            LeafExpression(field="study_name", operator=Operator.EQUALS, value=str(i))
            for i in range(MAX_EXPRESSIONS + 5)
        )
        expr = GroupExpression(connector="AND", children=leaves)
        with pytest.raises(ValidationError, match="exceeded"):
            validate_expression(Study, expr)


# ---------------------------------------------------------------------------
# Query builder — SQL clause compilation
# ---------------------------------------------------------------------------


class TestBuildClause:
    def test_equals(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.EQUALS, value="test")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'test'" in compiled

    def test_not_equals(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.NOT_EQUALS, value="test")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "!=" in compiled or "<>" in compiled
        assert "'test'" in compiled

    def test_greater_than(self) -> None:
        expr = LeafExpression(
            field="start_date", operator=Operator.GREATER_THAN, value=date(2023, 1, 1)
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert ">" in compiled

    def test_greater_than_or_equal(self) -> None:
        expr = LeafExpression(
            field="start_date", operator=Operator.GREATER_THAN_OR_EQUAL, value=date(2023, 1, 1)
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert ">=" in compiled

    def test_less_than(self) -> None:
        expr = LeafExpression(
            field="start_date", operator=Operator.LESS_THAN, value=date(2024, 1, 1)
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "<" in compiled
        assert ">" not in compiled

    def test_less_than_or_equal(self) -> None:
        expr = LeafExpression(
            field="start_date", operator=Operator.LESS_THAN_OR_EQUAL, value=date(2024, 1, 1)
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "<=" in compiled

    def test_between(self) -> None:
        expr = LeafExpression(
            field="start_date",
            operator=Operator.BETWEEN,
            value=[date(2023, 1, 1), date(2024, 1, 1)],
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "BETWEEN" in compiled.upper()

    def test_in(self) -> None:
        expr = LeafExpression(field="status", operator=Operator.IN, value=["active", "pending"])
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'active'" in compiled
        assert "'pending'" in compiled

    def test_not_in(self) -> None:
        expr = LeafExpression(field="status", operator=Operator.NOT_IN, value=["closed"])
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "NOT" in compiled.upper()
        assert "'closed'" in compiled

    def test_is_null(self) -> None:
        expr = LeafExpression(field="description", operator=Operator.IS_NULL)
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NULL" in compiled.upper()

    def test_is_not_null(self) -> None:
        expr = LeafExpression(field="description", operator=Operator.IS_NOT_NULL)
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NOT NULL" in compiled.upper()

    def test_like(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.LIKE, value="%test%")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in compiled.upper()

    def test_ilike(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.ILIKE, value="%test%")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "lower(studies.study_name) like lower('%test%')" in compiled.lower()

    def test_starts_with(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.STARTS_WITH, value="test")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "like" in compiled.lower()
        assert "'test' || '%'" in compiled or "'test%'" in compiled

    def test_ends_with(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.ENDS_WITH, value="test")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "like" in compiled.lower()
        assert "'%' || 'test'" in compiled or "'%test'" in compiled

    def test_contains(self) -> None:
        expr = LeafExpression(field="study_name", operator=Operator.CONTAINS, value="test")
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "like" in compiled.lower()
        assert "'%' || 'test' || '%'" in compiled or "'%test%'" in compiled


class TestBuildNestedClauses:
    def test_and_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="y"),
            ),
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'x'" in compiled
        assert "'y'" in compiled
        assert "AND" in compiled.upper()

    def test_or_group(self) -> None:
        expr = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="y"),
            ),
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'x'" in compiled
        assert "'y'" in compiled
        assert "OR" in compiled.upper()

    def test_negated_and_group(self) -> None:
        expr = GroupExpression(
            connector="AND",
            children=(LeafExpression(field="status", operator=Operator.EQUALS, value="closed"),),
            negated=True,
        )
        clause = build_clause(Study, expr)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'closed'" in compiled
        assert "!=" in compiled or "<>" in compiled

    def test_nested_or_inside_and(self) -> None:
        inner = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="status", operator=Operator.EQUALS, value="a"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="b"),
            ),
        )
        outer = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="main"),
                inner,
            ),
        )
        clause = build_clause(Study, outer)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'main'" in compiled
        assert "'a'" in compiled
        assert "'b'" in compiled

    def test_triple_nested(self) -> None:
        deepest = GroupExpression(
            connector="OR",
            children=(
                LeafExpression(field="status", operator=Operator.EQUALS, value="x"),
                LeafExpression(field="status", operator=Operator.EQUALS, value="y"),
            ),
        )
        middle = GroupExpression(
            connector="AND",
            children=(
                LeafExpression(field="study_name", operator=Operator.EQUALS, value="test"),
                deepest,
            ),
        )
        outer = GroupExpression(
            connector="AND",
            children=(
                middle,
                LeafExpression(field="organism", operator=Operator.EQUALS, value="human"),
            ),
        )
        clause = build_clause(Study, outer)
        compiled = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "'test'" in compiled
        assert "'human'" in compiled
        assert "'x'" in compiled
        assert "'y'" in compiled


# ---------------------------------------------------------------------------
# Schema serialisation / deserialisation
# ---------------------------------------------------------------------------


class TestAdvancedFilterRuleSchema:
    def test_minimal(self) -> None:
        rule = AdvancedFilterRule(field="study_name", operator="equals", value="test")
        assert rule.field == "study_name"
        assert rule.operator == "equals"
        assert rule.value == "test"

    def test_is_null(self) -> None:
        rule = AdvancedFilterRule(field="description", operator="is_null")
        assert rule.operator == "is_null"

    def test_is_not_null(self) -> None:
        rule = AdvancedFilterRule(field="description", operator="is_not_null")
        assert rule.operator == "is_not_null"

    def test_between(self) -> None:
        rule = AdvancedFilterRule(
            field="start_date", operator="between", value=["2023-01-01", "2024-01-01"]
        )
        assert rule.operator == "between"
        assert len(rule.value) == 2

    def test_in(self) -> None:
        rule = AdvancedFilterRule(field="status", operator="in", value=["active", "pending"])
        assert len(rule.value) == 2

    def test_all_operators_accepted(self) -> None:
        for op in Operator:
            if op in (Operator.IS_NULL, Operator.IS_NOT_NULL):
                AdvancedFilterRule(field="status", operator=op.value)
            elif op in OPERATORS_REQUIRING_LIST:
                AdvancedFilterRule(field="status", operator=op.value, value=["a", "b"])
            else:
                AdvancedFilterRule(field="status", operator=op.value, value="x")


class TestAdvancedFilterGroupSchema:
    def test_simple_group(self) -> None:
        group = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="x"),
                AdvancedFilterRule(field="status", operator="equals", value="y"),
            ],
        )
        assert group.connector == "AND"
        assert not group.negated
        assert len(group.children) == 2

    def test_or_group(self) -> None:
        group = AdvancedFilterGroup(
            connector="OR",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="x"),
                AdvancedFilterRule(field="study_name", operator="equals", value="y"),
            ],
        )
        assert group.connector == "OR"

    def test_negated_group(self) -> None:
        group = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="status", operator="equals", value="closed")],
            negated=True,
        )
        assert group.negated

    def test_nested_group(self) -> None:
        group = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="main"),
                AdvancedFilterGroup(
                    connector="OR",
                    children=[
                        AdvancedFilterRule(field="status", operator="equals", value="a"),
                        AdvancedFilterRule(field="status", operator="equals", value="b"),
                    ],
                ),
            ],
        )
        assert len(group.children) == 2
        assert isinstance(group.children[1], AdvancedFilterGroup)

    def test_empty_group_children(self) -> None:
        group = AdvancedFilterGroup(connector="AND", children=[])
        assert group.children == []


class TestSearchRequestExtended:
    def test_advanced_filters_default_none(self) -> None:
        req = SearchRequest()
        assert req.advanced_filters is None

    def test_advanced_filters_with_group(self) -> None:
        req = SearchRequest(
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[AdvancedFilterRule(field="study_name", operator="equals", value="x")],
            ),
        )
        assert req.advanced_filters is not None
        assert req.advanced_filters.connector == "AND"

    def test_backward_compatible_simple_filters(self) -> None:
        req = SearchRequest(filters=[FilterRule(field="study_name", operator="equals", value="x")])
        assert req.filters is not None
        assert req.filters[0].field == "study_name"


# ---------------------------------------------------------------------------
# Schema-to-expression conversion
# ---------------------------------------------------------------------------


class TestConvertToExpression:
    def test_simple_group(self) -> None:
        schema = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="study_name", operator="equals", value="x")],
        )
        expr = _convert_to_expression(schema)
        assert isinstance(expr, GroupExpression)
        assert expr.connector == "AND"
        assert len(expr.children) == 1
        leaf = expr.children[0]
        assert isinstance(leaf, LeafExpression)
        assert leaf.field == "study_name"
        assert leaf.operator == Operator.EQUALS
        assert leaf.value == "x"

    def test_nested_group(self) -> None:
        schema = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="main"),
                AdvancedFilterGroup(
                    connector="OR",
                    children=[AdvancedFilterRule(field="status", operator="equals", value="a")],
                ),
            ],
        )
        expr = _convert_to_expression(schema)
        assert len(expr.children) == 2
        assert isinstance(expr.children[1], GroupExpression)
        assert expr.children[1].connector == "OR"


# ---------------------------------------------------------------------------
# Repository integration
# ---------------------------------------------------------------------------


class TestApplyAdvancedFilters:
    def test_equals_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="study_name", operator="equals", value="test")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "'test'" in compiled

    def test_not_equals_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="study_name", operator="not_equals", value="test")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "!=" in compiled or "<>" in compiled

    def test_greater_than_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="start_date", operator="greater_than", value="2023-01-01")
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert ">" in compiled

    def test_between_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(
                    field="start_date", operator="between", value=["2023-01-01", "2024-01-01"]
                )
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "BETWEEN" in compiled.upper()

    def test_in_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="status", operator="in", value=["active", "pending"])
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "'active'" in compiled

    def test_not_in_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="status", operator="not_in", value=["closed"])],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "NOT" in compiled.upper()

    def test_is_null_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="description", operator="is_null")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NULL" in compiled.upper()

    def test_is_not_null_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="description", operator="is_not_null")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NOT NULL" in compiled.upper()

    def test_like_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="study_name", operator="like", value="%test%")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in compiled.upper()

    def test_ilike_filter(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="study_name", operator="ilike", value="%test%")],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "lower(studies.study_name) like lower('%test%')" in compiled.lower()

    def test_or_group(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="OR",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="x"),
                AdvancedFilterRule(field="study_name", operator="equals", value="y"),
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "OR" in compiled.upper()

    def test_and_group(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="x"),
                AdvancedFilterRule(field="status", operator="equals", value="y"),
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "AND" in compiled.upper()

    def test_negated_group(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="status", operator="equals", value="closed")],
            negated=True,
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "'closed'" in compiled
        assert "!=" in compiled or "<>" in compiled

    def test_nested_or_inside_and(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="study_name", operator="equals", value="main"),
                AdvancedFilterGroup(
                    connector="OR",
                    children=[
                        AdvancedFilterRule(field="status", operator="equals", value="a"),
                        AdvancedFilterRule(field="status", operator="equals", value="b"),
                    ],
                ),
            ],
        )
        result = apply_advanced_filters(stmt, Study, adv)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "'main'" in compiled
        assert "'a'" in compiled
        assert "'b'" in compiled

    def test_invalid_field_raises(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[AdvancedFilterRule(field="nonexistent", operator="equals", value="x")],
        )
        with pytest.raises(ValidationError, match="nonexistent"):
            apply_advanced_filters(stmt, Study, adv)

    def test_empty_group_raises(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(connector="AND", children=[])
        with pytest.raises(ValidationError, match="at least one child"):
            apply_advanced_filters(stmt, Study, adv)

    def test_between_invalid_value_raises(self) -> None:
        stmt = select(Study)
        adv = AdvancedFilterGroup(
            connector="AND",
            children=[
                AdvancedFilterRule(field="start_date", operator="between", value="not-a-list")
            ],
        )
        with pytest.raises(ValidationError, match="requires a list"):
            apply_advanced_filters(stmt, Study, adv)


class TestExecuteSearchWithAdvancedFilters:
    @pytest.mark.asyncio
    async def test_with_advanced_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=10),
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[
                    AdvancedFilterRule(field="study_name", operator="equals", value="Test Study")
                ],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.total_count == 1
        assert result.page == 1
        assert result.items == ["item"]

    @pytest.mark.asyncio
    async def test_advanced_filters_empty_result(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[
                    AdvancedFilterRule(
                        field="study_name", operator="equals", value="__nonexistent__"
                    )
                ],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.total_count == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_advanced_filters_with_simple_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["a", "b"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            filters=[FilterRule(field="study_name", operator="contains", value="Study")],
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[AdvancedFilterRule(field="status", operator="is_not_null")],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_advanced_filters_or_group(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            advanced_filters=AdvancedFilterGroup(
                connector="OR",
                children=[
                    AdvancedFilterRule(field="study_name", operator="equals", value="Alpha"),
                    AdvancedFilterRule(field="study_name", operator="equals", value="Beta"),
                ],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_advanced_filters_with_pagination(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 10

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["a", "b"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=5),
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[AdvancedFilterRule(field="study_name", operator="is_not_null")],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.page == 1
        assert result.page_size == 5

    @pytest.mark.asyncio
    async def test_advanced_filters_with_sort(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            sort=SortRequest(sort_by="study_name", sort_order="asc"),
            advanced_filters=AdvancedFilterGroup(
                connector="AND",
                children=[AdvancedFilterRule(field="study_name", operator="is_not_null")],
            ),
        )
        result = await execute_search(session, Study, request, select(Study))
        assert result.total_count == 1
