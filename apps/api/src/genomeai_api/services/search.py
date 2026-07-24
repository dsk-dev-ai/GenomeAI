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
from genomeai_api.repositories.search import (
    execute_suggestions as _execute_suggestions,
)
from genomeai_api.schemas.search import (
    FullTextSearchConfig,
    FullTextSearchResponse,
    HighlightedMatch,
    PaginationResponse,
    SearchRequest,
    SearchResponse,
    SuggestionItem,
    SuggestionResponse,
)
from genomeai_api.search.cache import SuggestionCache, suggestion_cache_key
from genomeai_api.search.suggestions import Suggestion, rank_suggestions

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

    async def suggest(
        self,
        model: type[M],
        column_name: str,
        query: str,
        limit: int = 10,
        domain: str = "study",
        cache: SuggestionCache | None = None,
    ) -> SuggestionResponse:
        cache_key = suggestion_cache_key(domain, column_name, query, limit)
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                return SuggestionResponse(
                    suggestions=[SuggestionItem(**s) for s in cached],
                    count=len(cached),
                    query=query,
                )

        raw_values = await _execute_suggestions(
            self._session,
            model,
            column_name,
            query,
            limit,
        )
        ranked: list[Suggestion] = rank_suggestions(raw_values, query, domain, column_name)
        items = [
            SuggestionItem(
                domain=s.domain,
                field=s.field,
                value=s.value,
                rank=s.rank,
                match_type=s.match_type.value,
            )
            for s in ranked
        ]

        if cache is not None:
            cache.set(cache_key, [item.model_dump() for item in items], ttl=300)

        return SuggestionResponse(
            suggestions=items,
            count=len(items),
            query=query,
        )
