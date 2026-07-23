from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.repositories.search import (
    SearchResult,
    _validate_filter_field,
    _validate_filter_value,
    _validate_sort_by,
    apply_filter,
    apply_filters,
    apply_pagination,
    apply_sorting,
    execute_search,
)
from genomeai_api.schemas.search import (
    FilterRule,
    SearchRequest,
    SortRequest,
)
from sqlalchemy import select


class TestSearchResult:
    def test_total_pages_exact_division(self) -> None:
        r = SearchResult(total_count=20, page_size=10, page=1)
        assert r.total_pages == 2

    def test_total_pages_round_up(self) -> None:
        r = SearchResult(total_count=21, page_size=10, page=1)
        assert r.total_pages == 3

    def test_total_pages_zero_items(self) -> None:
        r = SearchResult(total_count=0, page_size=20, page=1)
        assert r.total_pages == 1

    def test_has_next_true(self) -> None:
        r = SearchResult(total_count=50, page_size=20, page=1)
        assert r.has_next is True

    def test_has_next_false(self) -> None:
        r = SearchResult(total_count=20, page_size=20, page=1)
        assert r.has_next is False

    def test_has_previous_true(self) -> None:
        r = SearchResult(total_count=50, page_size=20, page=2)
        assert r.has_previous is True

    def test_has_previous_false(self) -> None:
        r = SearchResult(total_count=50, page_size=20, page=1)
        assert r.has_previous is False


class TestApplyPagination:
    def test_first_page(self) -> None:
        stmt = select(Study)
        result = apply_pagination(stmt, page=1, page_size=20)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT 20" in compiled
        assert "OFFSET 0" in compiled

    def test_second_page(self) -> None:
        stmt = select(Study)
        result = apply_pagination(stmt, page=2, page_size=10)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT 10" in compiled
        assert "OFFSET 10" in compiled

    def test_large_offset(self) -> None:
        stmt = select(Study)
        result = apply_pagination(stmt, page=10, page_size=5)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "LIMIT 5" in compiled
        assert "OFFSET 45" in compiled


class TestApplySorting:
    def test_ascending(self) -> None:
        stmt = select(Study)
        sort = SortRequest(sort_by="study_id", sort_order="asc")
        result = apply_sorting(stmt, Study, sort)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY" in compiled
        assert "studies.study_id" in compiled
        assert "ASC" in compiled.upper()

    def test_descending(self) -> None:
        stmt = select(Study)
        sort = SortRequest(sort_by="created_at", sort_order="desc")
        result = apply_sorting(stmt, Study, sort)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY" in compiled
        assert "studies.created_at" in compiled
        assert "DESC" in compiled.upper()

    def test_invalid_field_raises(self) -> None:
        stmt = select(Study)
        sort = SortRequest(sort_by="nonexistent", sort_order="asc")
        with pytest.raises(ValueError, match="Invalid sort field"):
            apply_sorting(stmt, Study, sort)


class TestApplyFilter:
    def test_equals(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="study_id", operator="equals", value="STU-001")
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "study_id" in compiled
        assert "STU-001" in compiled

    def test_contains(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="study_name", operator="contains", value="cancer")
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "study_name" in compiled
        assert "cancer" in compiled

    def test_starts_with(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="study_id", operator="starts_with", value="STU")
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "study_id" in compiled
        assert "STU" in compiled

    def test_ends_with(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="study_id", operator="ends_with", value="001")
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "study_id" in compiled
        assert "001" in compiled

    def test_in_operator(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="status", operator="in", value=["active", "completed"])
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "status" in compiled

    def test_in_operator_invalid_value(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="status", operator="in", value="not-a-list")
        with pytest.raises(TypeError, match="must be a list"):
            apply_filter(stmt, Study, rule)

    def test_is_null_true(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="description", operator="is_null", value=True)
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "description" in compiled
        assert "NULL" in compiled.upper()

    def test_is_null_false(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="description", operator="is_null", value=False)
        result = apply_filter(stmt, Study, rule)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "description" in compiled
        assert "NOT NULL" in compiled.upper()

    def test_invalid_field_raises(self) -> None:
        stmt = select(Study)
        rule = FilterRule(field="nonexistent", operator="equals", value="x")
        with pytest.raises(ValueError, match="Invalid filter field"):
            apply_filter(stmt, Study, rule)


class TestApplyFilters:
    def test_multiple_filters(self) -> None:
        stmt = select(Study)
        rules = [
            FilterRule(field="status", operator="equals", value="active"),
            FilterRule(field="study_name", operator="contains", value="cancer"),
        ]
        result = apply_filters(stmt, Study, rules)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "status" in compiled
        assert "study_name" in compiled

    def test_empty_filters(self) -> None:
        stmt = select(Study)
        result = apply_filters(stmt, Study, [])
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "SELECT" in compiled


class TestValidateSortBy:
    def test_valid_field(self) -> None:
        _validate_sort_by(Study, "study_id")

    def test_invalid_field(self) -> None:
        with pytest.raises(ValueError, match="Invalid sort field"):
            _validate_sort_by(Study, "nonexistent")


class TestValidateFilterField:
    def test_valid_field(self) -> None:
        _validate_filter_field(Study, "status")

    def test_invalid_field(self) -> None:
        with pytest.raises(ValueError, match="Invalid filter field"):
            _validate_filter_field(Study, "nonexistent")


class TestValidateFilterValue:
    def test_in_operator_valid(self) -> None:
        rule = FilterRule(field="status", operator="in", value=["a", "b"])
        _validate_filter_value(rule)

    def test_in_operator_invalid(self) -> None:
        rule = FilterRule(field="status", operator="in", value="not-a-list")
        with pytest.raises(TypeError, match="must be a list"):
            _validate_filter_value(rule)

    def test_non_in_operator_skipped(self) -> None:
        rule = FilterRule(field="status", operator="equals", value="x")
        _validate_filter_value(rule)


class TestExecuteSearch:
    @pytest.mark.asyncio
    async def test_basic_search(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 5

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["a", "b"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        request = SearchRequest()
        result = await execute_search(session, Study, request, select(Study))

        assert result.total_count == 5
        assert result.items == ["a", "b"]

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        session.execute = AsyncMock(return_value=count_result)

        request = SearchRequest(
            filters=[FilterRule(field="status", operator="equals", value="active")],
        )
        result = await execute_search(session, Study, request, select(Study))

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

        request = SearchRequest()
        result = await execute_search(session, Study, request, select(Study))

        assert result.total_count == 0
        assert result.items == []
