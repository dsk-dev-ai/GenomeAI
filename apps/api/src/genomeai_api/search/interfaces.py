from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


class SearchBackend(ABC):
    @abstractmethod
    async def search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any: ...

    @abstractmethod
    async def search_fts(
        self,
        model: type[Any],
        request: Any,
        fts_config: Any,
        base_stmt: Any = None,
    ) -> Any: ...

    @abstractmethod
    async def suggest(
        self,
        model: type[Any],
        column_name: str,
        query: str,
        limit: int = 10,
    ) -> list[str]: ...

    @abstractmethod
    async def coordinate_search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

    @abstractmethod
    async def index_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def update_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def delete_document(self, index: str, document_id: str) -> None: ...

    @abstractmethod
    async def bulk_index(
        self, index: str, documents: list[dict[str, Any]]
    ) -> None: ...

    @abstractmethod
    async def search_dsl(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any: ...


class SupportsHealthCheck(Protocol):
    async def health_check(self) -> bool: ...


class SupportsSearch(Protocol):
    async def search(
        self,
        model: type[Any],
        request: Any,
        base_stmt: Any = None,
    ) -> Any: ...


class SupportsIndexManagement(Protocol):
    async def index_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None: ...

    async def update_document(
        self, index: str, document_id: str, document: dict[str, Any]
    ) -> None: ...

    async def delete_document(self, index: str, document_id: str) -> None: ...

    async def bulk_index(
        self, index: str, documents: list[dict[str, Any]]
    ) -> None: ...
