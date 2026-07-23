from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from genomeai_api.models.study import Study
from genomeai_api.schemas.search import (
    PaginationRequest,
    SearchRequest,
    SearchResponse,
    SortRequest,
)
from genomeai_api.services.search import SearchService


class TestSearchService:
    @pytest.mark.asyncio
    async def test_search_returns_search_response(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        data_scalar = MagicMock()
        data_scalar.all.return_value = ["item"]
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=10),
        )
        result = await service.search(Study, request)

        assert isinstance(result, SearchResponse)
        assert result.items == ["item"]
        assert result.pagination.page == 1
        assert result.pagination.page_size == 10
        assert result.pagination.total_count == 1
        assert result.pagination.total_pages == 1
        assert result.pagination.has_next is False
        assert result.pagination.has_previous is False

    @pytest.mark.asyncio
    async def test_search_with_sort(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = SearchRequest(
            sort=SortRequest(sort_by="study_id", sort_order="asc"),
        )
        result = await service.search(Study, request)

        assert isinstance(result, SearchResponse)

    @pytest.mark.asyncio
    async def test_search_with_filters(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = SearchRequest(
            filters=[{"field": "status", "operator": "equals", "value": "active"}],
        )
        result = await service.search(Study, request)

        assert isinstance(result, SearchResponse)

    @pytest.mark.asyncio
    async def test_search_empty_result(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        data_scalar = MagicMock()
        data_scalar.all.return_value = []
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = SearchRequest()
        result = await service.search(Study, request)

        assert result.items == []
        assert result.pagination.total_count == 0

    @pytest.mark.asyncio
    async def test_search_handles_pagination_properties(self) -> None:
        session = AsyncMock(spec=["execute"])

        count_result = MagicMock()
        count_result.scalar_one.return_value = 25

        data_scalar = MagicMock()
        data_scalar.all.return_value = list(range(10))
        data_result = MagicMock()
        data_result.scalars.return_value = data_scalar

        session.execute = AsyncMock(side_effect=[count_result, data_result])

        service = SearchService(session)
        request = SearchRequest(
            pagination=PaginationRequest(page=1, page_size=10),
        )
        result = await service.search(Study, request)

        assert result.pagination.total_count == 25
        assert result.pagination.total_pages == 3
        assert result.pagination.has_next is True
        assert result.pagination.has_previous is False
