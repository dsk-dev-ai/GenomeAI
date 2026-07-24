from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SuggestionCacheEntry:
    suggestions: list[dict[str, Any]]
    ttl: int


class SuggestionCache(ABC):
    @abstractmethod
    def get(self, key: str) -> list[dict[str, Any]] | None:
        ...

    @abstractmethod
    def set(self, key: str, suggestions: list[dict[str, Any]], ttl: int) -> None:
        ...

    @abstractmethod
    def invalidate(self, key: str) -> None:
        ...


class NullCache(SuggestionCache):
    def get(self, key: str) -> list[dict[str, Any]] | None:
        return None

    def set(self, key: str, suggestions: list[dict[str, Any]], ttl: int) -> None:
        pass

    def invalidate(self, key: str) -> None:
        pass


class MemoryCache(SuggestionCache):
    def __init__(self) -> None:
        self._store: dict[str, SuggestionCacheEntry] = {}

    def get(self, key: str) -> list[dict[str, Any]] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        return entry.suggestions

    def set(self, key: str, suggestions: list[dict[str, Any]], ttl: int) -> None:
        self._store[key] = SuggestionCacheEntry(suggestions=suggestions, ttl=ttl)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)


def suggestion_cache_key(domain: str, field: str, query: str, limit: int) -> str:
    return f"suggest:{domain}:{field}:{query}:{limit}"
