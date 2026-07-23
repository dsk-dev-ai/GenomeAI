from __future__ import annotations

import pytest
from genomeai_api.schemas.search import (
    FilterRule,
    PaginationRequest,
    PaginationResponse,
    SearchRequest,
    SearchResponse,
    SortRequest,
)
from pydantic import ValidationError


class TestPaginationRequest:
    def test_defaults(self) -> None:
        p = PaginationRequest()
        assert p.page == 1
        assert p.page_size == 20

    def test_custom_values(self) -> None:
        p = PaginationRequest(page=3, page_size=50)
        assert p.page == 3
        assert p.page_size == 50

    def test_page_min(self) -> None:
        with pytest.raises(ValidationError):
            PaginationRequest(page=0)

    def test_page_size_min(self) -> None:
        with pytest.raises(ValidationError):
            PaginationRequest(page_size=0)

    def test_page_size_max(self) -> None:
        with pytest.raises(ValidationError):
            PaginationRequest(page_size=101)

    def test_page_size_at_limit(self) -> None:
        p = PaginationRequest(page_size=100)
        assert p.page_size == 100


class TestPaginationResponse:
    def test_first_page_no_next(self) -> None:
        r = PaginationResponse(
            page=1, page_size=20, total_count=10, total_pages=1,
            has_next=False, has_previous=False,
        )
        assert r.page == 1
        assert r.total_count == 10
        assert r.total_pages == 1
        assert r.has_next is False
        assert r.has_previous is False

    def test_middle_page(self) -> None:
        r = PaginationResponse(
            page=2, page_size=10, total_count=25, total_pages=3,
            has_next=True, has_previous=True,
        )
        assert r.has_next is True
        assert r.has_previous is True

    def test_last_page(self) -> None:
        r = PaginationResponse(
            page=3, page_size=10, total_count=25, total_pages=3,
            has_next=False, has_previous=True,
        )
        assert r.has_next is False
        assert r.has_previous is True


class TestSortRequest:
    def test_valid(self) -> None:
        s = SortRequest(sort_by="created_at", sort_order="desc")
        assert s.sort_by == "created_at"
        assert s.sort_order == "desc"

    def test_default_order(self) -> None:
        s = SortRequest(sort_by="name")
        assert s.sort_order == "asc"

    def test_empty_sort_by(self) -> None:
        with pytest.raises(ValidationError):
            SortRequest(sort_by="")

    def test_invalid_sort_order(self) -> None:
        with pytest.raises(ValidationError):
            SortRequest(sort_by="name", sort_order="invalid")


class TestFilterRule:
    def test_equals(self) -> None:
        f = FilterRule(field="status", operator="equals", value="active")
        assert f.field == "status"
        assert f.operator == "equals"
        assert f.value == "active"

    def test_contains(self) -> None:
        f = FilterRule(field="name", operator="contains", value="genome")
        assert f.operator == "contains"

    def test_starts_with(self) -> None:
        f = FilterRule(field="name", operator="starts_with", value="PRJ")
        assert f.operator == "starts_with"

    def test_ends_with(self) -> None:
        f = FilterRule(field="name", operator="ends_with", value="001")
        assert f.operator == "ends_with"

    def test_in_operator(self) -> None:
        f = FilterRule(field="status", operator="in", value=["active", "completed"])
        assert f.operator == "in"
        assert f.value == ["active", "completed"]

    def test_is_null(self) -> None:
        f = FilterRule(field="description", operator="is_null", value=True)
        assert f.operator == "is_null"
        assert f.value is True

    def test_is_not_null(self) -> None:
        f = FilterRule(field="description", operator="is_null", value=False)
        assert f.value is False

    def test_empty_field(self) -> None:
        with pytest.raises(ValidationError):
            FilterRule(field="", operator="equals", value="x")


class TestSearchRequest:
    def test_defaults(self) -> None:
        r = SearchRequest()
        assert r.pagination.page == 1
        assert r.pagination.page_size == 20
        assert r.sort is None
        assert r.filters is None

    def test_with_sort(self) -> None:
        r = SearchRequest(
            sort={"sort_by": "created_at", "sort_order": "desc"},
        )
        assert r.sort is not None
        assert r.sort.sort_by == "created_at"

    def test_with_filters(self) -> None:
        r = SearchRequest(
            filters=[
                {"field": "status", "operator": "equals", "value": "active"},
            ],
        )
        assert r.filters is not None
        assert len(r.filters) == 1
        assert r.filters[0].field == "status"

    def test_with_pagination(self) -> None:
        r = SearchRequest(pagination={"page": 2, "page_size": 50})
        assert r.pagination.page == 2
        assert r.pagination.page_size == 50

    def test_with_pagination_none(self) -> None:
        r = SearchRequest(pagination=None)
        assert r.pagination.page == 1
        assert r.pagination.page_size == 20

    def test_empty_pagination_dict(self) -> None:
        r = SearchRequest(pagination={})
        assert r.pagination.page == 1
        assert r.pagination.page_size == 20


class TestSearchResponse:
    def test_empty(self) -> None:
        pagination = PaginationResponse(
            page=1, page_size=20, total_count=0, total_pages=1,
            has_next=False, has_previous=False,
        )
        r = SearchResponse(items=[], pagination=pagination)
        assert r.items == []
        assert r.pagination.total_count == 0

    def test_with_items(self) -> None:
        pagination = PaginationResponse(
            page=1, page_size=20, total_count=2, total_pages=1,
            has_next=False, has_previous=False,
        )
        r = SearchResponse(items=["a", "b"], pagination=pagination)
        assert r.items == ["a", "b"]
        assert r.pagination.total_count == 2
