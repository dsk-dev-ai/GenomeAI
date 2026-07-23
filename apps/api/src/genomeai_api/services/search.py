from __future__ import annotations

from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.repositories.search import (
    SearchResult,
)
from genomeai_api.repositories.search import (
    execute_search as _execute_search,
)
from genomeai_api.schemas.search import (
    PaginationResponse,
    SearchRequest,
    SearchResponse,
)

M = TypeVar("M", bound=DeclarativeBase)


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        model: type[M],
        request: SearchRequest,
        base_stmt: Select[tuple[M]] | None = None,
    ) -> SearchResponse:
        stmt = base_stmt if base_stmt is not None else select(model)
        result: SearchResult[M] = await _execute_search(
            self._session, model, request, stmt
        )
        return SearchResponse(
            items=result.items,
            pagination=PaginationResponse(
                page=result.page,
                page_size=result.page_size,
                total_count=result.total_count,
                total_pages=result.total_pages,
                has_next=result.has_next,
                has_previous=result.has_previous,
            ),
        )
