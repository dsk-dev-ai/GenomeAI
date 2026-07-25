from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.repositories.search import execute_dsl_search
from genomeai_api.schemas.search import (
    FilterRule,
    PaginationRequest,
    SearchRequest,
    SortRequest,
)
from genomeai_api.search.dsl_compiler import (
    DSL_OP_MAP,
    SUPPORTED_DSL_OPS,
    compile_dsl,
)
from genomeai_api.search.dsl_types import DslSearchQuery
from genomeai_api.search.expressions import GroupExpression, LeafExpression
from genomeai_api.search.operators import Operator
from genomeai_api.search.validation import ValidationError
from sqlalchemy import select


class TestDslOperatorMap:
    def test_all_operators_mapped(self) -> None:
        assert DSL_OP_MAP["eq"] is Operator.EQUALS
        assert DSL_OP_MAP["ne"] is Operator.NOT_EQUALS
        assert DSL_OP_MAP["gt"] is Operator.GREATER_THAN
        assert DSL_OP_MAP["gte"] is Operator.GREATER_THAN_OR_EQUAL
        assert DSL_OP_MAP["lt"] is Operator.LESS_THAN
        assert DSL_OP_MAP["lte"] is Operator.LESS_THAN_OR_EQUAL
        assert DSL_OP_MAP["between"] is Operator.BETWEEN
        assert DSL_OP_MAP["in"] is Operator.IN
        assert DSL_OP_MAP["not_in"] is Operator.NOT_IN
        assert DSL_OP_MAP["is_null"] is Operator.IS_NULL
        assert DSL_OP_MAP["is_not_null"] is Operator.IS_NOT_NULL
        assert DSL_OP_MAP["like"] is Operator.LIKE
        assert DSL_OP_MAP["ilike"] is Operator.ILIKE
        assert DSL_OP_MAP["starts_with"] is Operator.STARTS_WITH
        assert DSL_OP_MAP["ends_with"] is Operator.ENDS_WITH
        assert DSL_OP_MAP["contains"] is Operator.CONTAINS

    def test_supported_ops_is_frozenset(self) -> None:
        assert isinstance(SUPPORTED_DSL_OPS, frozenset)
        assert set(DSL_OP_MAP.keys()) == SUPPORTED_DSL_OPS


class TestDslSearchQuerySchema:
    def test_default_construction(self) -> None:
        query = DslSearchQuery()
        assert query.where == {}
        assert query.pagination.page == 1
        assert query.pagination.page_size == 20
        assert query.sort is None
        assert query.filters is None

    def test_with_all_fields(self) -> None:
        query = DslSearchQuery(
            where={"field": "study_name", "op": "eq", "value": "Test"},
            pagination=PaginationRequest(page=2, page_size=10),
            sort=SortRequest(sort_by="study_name", sort_order="asc"),
            filters=[FilterRule(field="status", operator="equals", value="active")],
        )
        assert query.where == {"field": "study_name", "op": "eq", "value": "Test"}
        assert query.pagination.page == 2
        assert query.pagination.page_size == 10
        assert query.sort is not None
        assert query.sort.sort_by == "study_name"  # type: ignore[union-attr]
        assert len(query.filters) == 1



class TestCompileDsl:
    def test_empty_where_raises(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            compile_dsl({}, Study)

    def test_non_dict_where_raises(self) -> None:
        with pytest.raises(ValidationError, match="must be a dict"):
            compile_dsl("not a dict", Study)

    def test_single_leaf_wraps_to_group(self) -> None:
        expr = compile_dsl(
            {"field": "study_name", "op": "eq", "value": "Test Study"}, Study
        )
        assert isinstance(expr, GroupExpression)
        assert len(expr.children) == 1
        leaf = expr.children[0]
        assert isinstance(leaf, LeafExpression)
        assert leaf.field == "study_name"
        assert leaf.operator is Operator.EQUALS
        assert leaf.value == "Test Study"

    def test_and_group(self) -> None:
        expr = compile_dsl(
            {
                "and": [
                    {"field": "study_name", "op": "eq", "value": "Alpha"},
                    {"field": "status", "op": "is_not_null"},
                ]
            },
            Study,
        )
        assert isinstance(expr, GroupExpression)
        assert expr.connector == "AND"
        assert len(expr.children) == 2
        assert isinstance(expr.children[0], LeafExpression)
        assert expr.children[0].field == "study_name"
        assert isinstance(expr.children[1], LeafExpression)
        assert expr.children[1].field == "status"

    def test_or_group(self) -> None:
        expr = compile_dsl(
            {
                "or": [
                    {"field": "study_name", "op": "eq", "value": "Alpha"},
                    {"field": "study_name", "op": "eq", "value": "Beta"},
                ]
            },
            Study,
        )
        assert isinstance(expr, GroupExpression)
        assert expr.connector == "OR"
        assert len(expr.children) == 2

    def test_not_wrapping_and(self) -> None:
        expr = compile_dsl(
            {
                "not": {
                    "and": [
                        {"field": "study_name", "op": "eq", "value": "Exclude"},
                    ]
                }
            },
            Study,
        )
        assert isinstance(expr, GroupExpression)
        assert expr.negated is True

    def test_not_wrapping_leaf(self) -> None:
        expr = compile_dsl(
            {"not": {"field": "study_name", "op": "eq", "value": "Exclude"}},
            Study,
        )
        assert isinstance(expr, GroupExpression)
        assert expr.negated is True
        assert len(expr.children) == 1

    def test_field_validation_rejects_invalid_field(self) -> None:
        with pytest.raises(ValidationError, match="not a mapped column"):
            compile_dsl({"field": "nonexistent_field", "op": "eq", "value": "x"}, Study)


class TestValidateNodeStructure:
    def test_empty_object(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            compile_dsl({}, Study)

    def test_unknown_keys(self) -> None:
        with pytest.raises(ValidationError, match="Unknown key"):
            compile_dsl({"field": "name", "op": "eq", "value": "x", "extra_key": 1}, Study)

    def test_mixed_logical_and_leaf(self) -> None:
        with pytest.raises(ValidationError, match="Mixed logical"):
            compile_dsl(
                {
                    "and": [{"field": "name", "op": "eq", "value": "x"}],
                    "field": "name",
                    "op": "eq",
                    "value": "y",
                },
                Study,
            )

    def test_no_valid_keys(self) -> None:
        with pytest.raises(ValidationError, match="Unknown key"):
            compile_dsl({"some_random_key": 123}, Study)

    def test_multiple_logical_keys(self) -> None:
        with pytest.raises(ValidationError, match="Multiple logical"):
            compile_dsl(
                {
                    "and": [{"field": "name", "op": "eq", "value": "x"}],
                    "or": [{"field": "name", "op": "eq", "value": "y"}],
                },
                Study,
            )

    def test_not_with_list(self) -> None:
        with pytest.raises(ValidationError, match="must be a single object"):
            compile_dsl(
                {
                    "not": [
                        {"field": "name", "op": "eq", "value": "x"},
                    ]
                },
                Study,
            )

    def test_missing_field(self) -> None:
        with pytest.raises(ValidationError, match="missing 'field'"):
            compile_dsl({"op": "eq", "value": "x"}, Study)

    def test_missing_op(self) -> None:
        with pytest.raises(ValidationError, match="missing 'op'"):
            compile_dsl({"field": "name", "value": "x"}, Study)

    def test_unsupported_operator(self) -> None:
        with pytest.raises(ValidationError, match="Unsupported operator"):
            compile_dsl({"field": "name", "op": "bad_op", "value": "x"}, Study)

    def test_operator_no_value_requires_no_value(self) -> None:
        with pytest.raises(ValidationError, match="does not accept a value"):
            compile_dsl({"field": "status", "op": "is_null", "value": "x"}, Study)

    def test_between_requires_list_of_two(self) -> None:
        with pytest.raises(ValidationError, match="requires exactly 2"):
            compile_dsl({"field": "patient_count", "op": "between", "value": [1]}, Study)

    def test_in_requires_non_empty_list(self) -> None:
        with pytest.raises(ValidationError, match="non-empty list"):
            compile_dsl({"field": "status", "op": "in", "value": []}, Study)

    def test_not_in_requires_non_empty_list(self) -> None:
        with pytest.raises(ValidationError, match="non-empty list"):
            compile_dsl({"field": "status", "op": "not_in", "value": []}, Study)

    def test_non_list_for_list_operator(self) -> None:
        with pytest.raises(ValidationError, match="requires a list value"):
            compile_dsl({"field": "status", "op": "in", "value": "not_a_list"}, Study)

    def test_operator_missing_value_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires a non-null value"):
            compile_dsl({"field": "study_name", "op": "eq"}, Study)


class TestDslNodeCompilation:
    def test_equal_operator(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl({"field": "study_name", "op": "eq", "value": "Test"}, Study)
        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "study_name" in sql
        assert "Test" in sql

    def test_like_operator(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl({"field": "study_name", "op": "like", "value": "%test%"}, Study)
        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in sql.upper()
        assert "%test%" in sql

    def test_between_operator(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl(
            {"field": "created_at", "op": "between", "value": ["2020-01-01", "2023-01-01"]}, Study
        )
        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "BETWEEN" in sql.upper()

    def test_in_operator(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl(
            {"field": "status", "op": "in", "value": ["active", "pending"]}, Study
        )
        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "IN" in sql.upper()
        assert "active" in sql

    def test_is_null_operator(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl({"field": "status", "op": "is_null"}, Study)
        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "IS NULL" in sql.upper()

    def test_complex_nested_group(self) -> None:
        from genomeai_api.search.query_builder import build_clause

        expr = compile_dsl(
            {
                "and": [
                    {"field": "study_name", "op": "contains", "value": "Cancer"},
                    {
                        "or": [
                            {"field": "status", "op": "eq", "value": "active"},
                            {"field": "status", "op": "eq", "value": "pending"},
                        ]
                    },
                    {"not": {"field": "description", "op": "is_null"}},
                ]
            },
            Study,
        )
        assert isinstance(expr, GroupExpression)
        assert expr.connector == "AND"
        assert len(expr.children) == 3

        clause = build_clause(Study, expr)
        sql = str(clause.compile(compile_kwargs={"literal_binds": True}))
        assert "Cancer" in sql
        assert "active" in sql
        assert "pending" in sql
        assert "IS NOT NULL" in sql.upper() or "ISNULL" in sql.upper()

    def test_recursion_depth_exceeded(self) -> None:
        deep: dict[str, object] = {"field": "name", "op": "eq", "value": "x"}
        current: dict[str, object] = {"not": deep}
        for _ in range(12):
            current = {"not": current}
        with pytest.raises(ValidationError, match="recursion depth"):
            compile_dsl(current, Study)


class TestExecuteDslSearch:
    @pytest.mark.asyncio
    async def test_basic_execution(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        dsl_expr = compile_dsl({"field": "study_name", "op": "eq", "value": "Test"}, Study)

        result = await execute_dsl_search(session, Study, request, dsl_expr)
        assert result.total_count == 1
        assert result.items == ["item"]

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["a", "b"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=10),
            filters=[FilterRule(field="study_name", operator="contains", value="Study")],
        )
        dsl_expr = compile_dsl({"field": "status", "op": "is_not_null"}, Study)

        result = await execute_dsl_search(session, Study, request, dsl_expr)
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_with_sort(self) -> None:
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
            sort=SortRequest(sort_by="study_name", sort_order="asc"),
        )
        dsl_expr = compile_dsl({"field": "study_name", "op": "is_not_null"}, Study)

        result = await execute_dsl_search(session, Study, request, dsl_expr)
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_with_base_stmt(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        dsl_expr = compile_dsl({"field": "study_name", "op": "eq", "value": "Test"}, Study)

        base_stmt = select(Study).where(Study.study_name.isnot(None))
        result = await execute_dsl_search(session, Study, request, dsl_expr, base_stmt)
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_empty_result(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest(pagination=PaginationRequest(page=1, page_size=10))
        dsl_expr = compile_dsl(
            {"field": "study_name", "op": "eq", "value": "__nonexistent__"}, Study
        )

        result = await execute_dsl_search(session, Study, request, dsl_expr)
        assert result.total_count == 0
        assert result.items == []


class TestSearchServiceDsl:
    @pytest.mark.asyncio
    async def test_search_dsl(self) -> None:
        from genomeai_api.repositories.search import execute_dsl_search as real_execute_dsl

        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = DslSearchQuery(
            where={"field": "study_name", "op": "eq", "value": "Test"},
        )

        result = await real_execute_dsl(
            session, Study, SearchRequest(pagination=request.pagination),
            compile_dsl(request.where, Study),
        )
        assert result.total_count == 1
        assert result.items == ["item"]
