"""Monarch Initiative REST client."""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

MONARCH_BASE_URL = "https://api-v3.monarchinitiative.org/v3"


class MonarchClient:
    """Async Monarch Initiative REST client with retry."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=MONARCH_BASE_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def _get_with_retry(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        retries: int = 3,
        delay: float = 2.0,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                response = await self._client.get(url, params=params)
                if response.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    continue
                return response
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    async def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """Full-text search across Monarch knowledge graph."""
        response = await self._get_with_retry(
            "/api/search",
            params={"q": query, "limit": limit},
        )
        if response.status_code != 200:
            return []
        data: object = response.json()
        if isinstance(data, dict):
            items_val: object = data.get("items")
            docs_val: object = data.get("docs")
            rows_val: object = data.get("rows")
            docs_raw: list[object] = (
                items_val if isinstance(items_val, list)
                else docs_val if isinstance(docs_val, list)
                else rows_val if isinstance(rows_val, list)
                else []
            )
            return [d for d in docs_raw if isinstance(d, dict)]
        return []

    async def get_entity(self, entity_id: str) -> dict[str, object] | None:
        """Get entity details by ID (e.g. 'MONDO:0007947')."""
        response = await self._get_with_retry(f"/api/entity/{entity_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def get_disease_associations(
        self,
        gene_id: str,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Get disease associations for a gene (HGNC or Ensembl ID)."""
        response = await self._get_with_retry(
            f"/api/entity/{gene_id}/diseases",
            params={"limit": limit},
        )
        if response.status_code != 200:
            return []
        data: object = response.json()
        if isinstance(data, dict):
            assoc_val: object = data.get("associations")
            items_val: object = data.get("items")
            rows_val: object = data.get("rows")
            rows_raw: list[object] = (
                assoc_val if isinstance(assoc_val, list)
                else items_val if isinstance(items_val, list)
                else rows_val if isinstance(rows_val, list)
                else []
            )
            return [r for r in rows_raw if isinstance(r, dict)]
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
        return []

    async def health_check(self) -> bool:
        try:
            response = await self._get_with_retry("/api/search", params={"q": "cancer", "limit": 1})
            return response.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
