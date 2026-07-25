from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.repositories.search import (
    FTSResult,
    SearchResult,
)
from genomeai_api.repositories.search import (
    execute_coordinate_search as _execute_coordinate_search,
)
from genomeai_api.repositories.search import (
    execute_dsl_search as _execute_dsl_search,
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
from genomeai_api.schemas.search import SearchRequest
from genomeai_api.search.dsl_compiler import compile_dsl
from genomeai_api.search.dsl_types import DslSearchQuery
from genomeai_api.search.interfaces import SearchBackend


class PostgresBackend(SearchBackend):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        model: type[DeclarativeBase],
        request: Any,
        base_stmt: Any = None,
    ) -> SearchResult[Any]:
        stmt: Select[Any] = base_stmt if base_stmt is not None else select(model)
        return await _execute_search(self._session, model, request, stmt)

    async def search_fts(
        self,
        model: type[DeclarativeBase],
        request: Any,
        fts_config: Any,
        base_stmt: Any = None,
    ) -> FTSResult[Any]:
        return await _execute_fts_search(
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

    async def suggest(
        self,
        model: type[DeclarativeBase],
        column_name: str,
        query: str,
        limit: int = 10,
    ) -> list[str]:
        return await _execute_suggestions(
            self._session, model, column_name, query, limit
        )

    async def coordinate_search(
        self,
        model: type[DeclarativeBase],
        request: Any,
        base_stmt: Any = None,
    ) -> SearchResult[Any]:
        return await _execute_coordinate_search(
            self._session, model, request, base_stmt
        )

    async def health_check(self) -> bool:
        try:
            await self._session.execute(select(1))
            return True
        except Exception:
            return False

    async def index_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        msg = "PostgresBackend does not support document indexing"
        raise NotImplementedError(msg)

    async def update_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        msg = "PostgresBackend does not support document indexing"
        raise NotImplementedError(msg)

    async def delete_document(self, index: str, document_id: str) -> None:
        msg = "PostgresBackend does not support document indexing"
        raise NotImplementedError(msg)

    async def bulk_index(
        self, index: str, documents: list[dict[str, Any]]
    ) -> None:
        msg = "PostgresBackend does not support document indexing"
        raise NotImplementedError(msg)

    async def search_dsl(
        self,
        model: type[DeclarativeBase],
        request: DslSearchQuery,
        base_stmt: Any = None,
    ) -> SearchResult[Any]:
        dsl_expr = compile_dsl(request.where, model)
        search_request = SearchRequest(
            pagination=request.pagination,
            sort=request.sort,
            filters=request.filters,
        )
        stmt = base_stmt if base_stmt is not None else select(model)
        return await _execute_dsl_search(
            self._session, model, search_request, dsl_expr, stmt
        )
