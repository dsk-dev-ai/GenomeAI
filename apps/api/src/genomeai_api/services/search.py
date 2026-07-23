from __future__ import annotations

from typing import TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.repositories.search import (
    FTSResult,
    SearchResult,
)
from genomeai_api.repositories.search import (
    execute_fts_search as _execute_fts_search,
)
from genomeai_api.repositories.search import (
    execute_search as _execute_search,
)
from genomeai_api.schemas.search import (
    FullTextSearchConfig,
    FullTextSearchResponse,
    HighlightedMatch,
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

    async def search_fts(
        self,
        model: type[M],
        request: SearchRequest,
        fts_config: FullTextSearchConfig,
        base_stmt: Select[tuple[M]] | None = None,
    ) -> FullTextSearchResponse:
        fts_result: FTSResult[M] = await _execute_fts_search(
            self._session,
            model,
            request,
            fts_columns=fts_config.columns,
            fts_query=fts_config.query,
            fts_config=fts_config.config,
            query_type=fts_config.query_type,
            weights=fts_config.weights,
            highlight_columns=fts_config.columns,
            base_stmt=base_stmt,
        )

        highlights: list[list[HighlightedMatch]] | None = None
        if fts_result.highlights is not None:
            highlights = [
                [HighlightedMatch(field=h[0], snippet=h[1]) for h in row]
                for row in fts_result.highlights
            ]

        return FullTextSearchResponse(
            items=fts_result.items,
            pagination=PaginationResponse(
                page=fts_result.page,
                page_size=fts_result.page_size,
                total_count=fts_result.total_count,
                total_pages=fts_result.total_pages,
                has_next=fts_result.has_next,
                has_previous=fts_result.has_previous,
            ),
            ranks=fts_result.ranks,
            highlights=highlights,
        )
