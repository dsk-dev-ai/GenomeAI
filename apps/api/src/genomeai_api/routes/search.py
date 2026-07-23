from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.dependencies import get_db_session
from genomeai_api.schemas.search import (
    FullTextSearchRequest,
    FullTextSearchResponse,
    SearchRequest,
    SearchResponse,
)
from genomeai_api.services.search import SearchService


def add_domain_search_routes(
    router: APIRouter,
    model: type[DeclarativeBase],
    _domain_name: str,
) -> None:
    search_name = f"search_{_domain_name}"
    fts_name = f"search_{_domain_name}_fts"

    @router.post("/search", response_model=SearchResponse, operation_id=search_name)
    async def search_domain(  # pyright: ignore[reportUnusedFunction]
        request: SearchRequest,
        session: AsyncSession = Depends(get_db_session),
    ) -> SearchResponse:
        service = SearchService(session)
        return await service.search(model, request)

    @router.post("/search/fts", response_model=FullTextSearchResponse, operation_id=fts_name)
    async def search_domain_fts(  # pyright: ignore[reportUnusedFunction]
        request: FullTextSearchRequest,
        session: AsyncSession = Depends(get_db_session),
    ) -> FullTextSearchResponse:
        service = SearchService(session)
        return await service.search_fts(model, request.search, request.fts)
