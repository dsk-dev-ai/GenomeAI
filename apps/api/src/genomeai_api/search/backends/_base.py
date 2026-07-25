from __future__ import annotations

import asyncio
from typing import Any

from genomeai_api.search.interfaces import SearchBackend


class BaseSearchEngineBackend(SearchBackend):
    def __init__(
        self,
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
        index_prefix: str = "genomeai",
    ) -> None:
        self._hosts = hosts or ["http://localhost:9200"]
        self._username = username
        self._password = password
        self._index_prefix = index_prefix
        self._client: Any = None

    def _get_client(self) -> Any:
        raise NotImplementedError

    def _prefixed_index(self, index: str) -> str:
        return f"{self._index_prefix}_{index}"

    async def search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = (
            f"{type(self).__name__}.search is not directly callable from SearchService. "
            "Use the search engine query DSL via index operations."
        )
        raise NotImplementedError(msg)

    async def search_fts(
        self,
        model: type[Any],
        request: Any,
        fts_config: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = f"{type(self).__name__} does not support PostgreSQL full-text search"
        raise NotImplementedError(msg)

    async def suggest(
        self,
        model: type[Any],
        column_name: str,
        query: str,
        limit: int = 10,
    ) -> list[str]:
        msg = f"{type(self).__name__} does not support PostgreSQL-based suggestions"
        raise NotImplementedError(msg)

    async def coordinate_search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = f"{type(self).__name__} does not support coordinate search"
        raise NotImplementedError(msg)

    async def search_dsl(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = f"{type(self).__name__} does not support DSL search"
        raise NotImplementedError(msg)

    async def index_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        client = self._get_client()
        full_index = self._prefixed_index(index)
        await asyncio.to_thread(
            lambda: client.index(index=full_index, id=document_id, body=document)
        )

    async def update_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        client = self._get_client()
        full_index = self._prefixed_index(index)
        await asyncio.to_thread(
            lambda: client.update(index=full_index, id=document_id, body={"doc": document})
        )

    async def delete_document(self, index: str, document_id: str) -> None:
        client = self._get_client()
        full_index = self._prefixed_index(index)
        await asyncio.to_thread(
            lambda: client.delete(index=full_index, id=document_id)
        )

    async def bulk_index(
        self, index: str, documents: list[dict[str, Any]]
    ) -> None:
        client = self._get_client()
        full_index = self._prefixed_index(index)
        bulk_body: list[dict[str, Any]] = []
        for doc in documents:
            doc_id = doc.get("_id")
            action: dict[str, Any] = {"index": {"_index": full_index}}
            if doc_id:
                action["index"]["_id"] = doc_id
            bulk_body.append(action)
            bulk_body.append(
                {k: v for k, v in doc.items() if k != "_id"}
            )
        if bulk_body:
            await asyncio.to_thread(lambda: client.bulk(body=bulk_body))
