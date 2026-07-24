from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from genomeai_api.schemas.search import SuggestionItem


@dataclass
class SuggestionCacheEntry:
    suggestions: list[SuggestionItem]
    expires_at: float


class SuggestionCache(ABC):
    @abstractmethod
    def get(self, key: str) -> list[SuggestionItem] | None:
        ...

    @abstractmethod
    def set(self, key: str, suggestions: list[SuggestionItem], ttl: int) -> None:
        ...

    @abstractmethod
    def invalidate(self, key: str) -> None:
        ...


class NullCache(SuggestionCache):
    def get(self, key: str) -> list[SuggestionItem] | None:
        return None

    def set(self, key: str, suggestions: list[SuggestionItem], ttl: int) -> None:
        pass

    def invalidate(self, key: str) -> None:
        pass


class MemoryCache(SuggestionCache):
    def __init__(self) -> None:
        self._store: dict[str, SuggestionCacheEntry] = {}

    def get(self, key: str) -> list[SuggestionItem] | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.suggestions

    def set(self, key: str, suggestions: list[SuggestionItem], ttl: int) -> None:
        self._store[key] = SuggestionCacheEntry(
            suggestions=suggestions,
            expires_at=time.monotonic() + ttl,
        )

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)


def suggestion_cache_key(domain: str, field: str, query: str, limit: int) -> str:
    return f"suggest:{domain}:{field}:{query}:{limit}"
