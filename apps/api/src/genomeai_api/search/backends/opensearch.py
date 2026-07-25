from __future__ import annotations

from typing import Any

from genomeai_api.search.interfaces import SearchBackend


class OpenSearchBackend(SearchBackend):
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
        if self._client is not None:
            return self._client
        try:
            from opensearchpy import OpenSearch  # type: ignore[import-untyped]

            kwargs: dict[str, Any] = {"hosts": self._hosts}
            if self._username and self._password:
                kwargs["http_auth"] = (self._username, self._password)
            self._client = OpenSearch(**kwargs)
            return self._client
        except ImportError:
            msg = "opensearch-py is not installed. Install with: pip install opensearch-py"
            raise ImportError(msg)

    async def search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = (
            "OpenSearchBackend.search is not directly callable from SearchService. "
            "Use the OpenSearch query DSL via index operations."
        )
        raise NotImplementedError(msg)

    async def search_fts(
        self,
        model: type[Any],
        request: Any,
        fts_config: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = "OpenSearchBackend does not support PostgreSQL full-text search"
        raise NotImplementedError(msg)

    async def suggest(
        self,
        model: type[Any],
        column_name: str,
        query: str,
        limit: int = 10,
    ) -> list[str]:
        msg = "OpenSearchBackend does not support PostgreSQL-based suggestions"
        raise NotImplementedError(msg)

    async def coordinate_search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any:
        msg = "OpenSearchBackend does not support coordinate search"
        raise NotImplementedError(msg)

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            info = client.info()
            return info.get("status", 0) == 200 or "cluster_name" in info
        except Exception:
            return False

    async def index_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        client = self._get_client()
        full_index = f"{self._index_prefix}_{index}"
        client.index(index=full_index, id=document_id, body=document)

    async def update_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None:
        client = self._get_client()
        full_index = f"{self._index_prefix}_{index}"
        client.update(index=full_index, id=document_id, body={"doc": document})

    async def delete_document(self, index: str, document_id: str) -> None:
        client = self._get_client()
        full_index = f"{self._index_prefix}_{index}"
        client.delete(index=full_index, id=document_id)

    async def bulk_index(
        self, index: str, documents: list[dict[str, Any]]
    ) -> None:
        client = self._get_client()
        full_index = f"{self._index_prefix}_{index}"
        bulk_body: list[dict[str, Any]] = []
        for doc in documents:
            doc_id = doc.pop("_id", None)
            action: dict[str, Any] = {"index": {"_index": full_index}}
            if doc_id:
                action["index"]["_id"] = doc_id
            bulk_body.append(action)
            bulk_body.append(doc)
        if bulk_body:
            client.bulk(body=bulk_body)
