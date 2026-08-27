"""Disease Ontology REST client."""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

DO_BASE_URL = "https://api.disease-ontology.org/v1"


class DiseaseOntologyClient:
    """Async Disease Ontology REST client with retry."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=DO_BASE_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def _get_with_retry(
        self,
        url: str,
        retries: int = 3,
        delay: float = 2.0,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                response = await self._client.get(url)
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

    async def _post_with_retry(
        self,
        url: str,
        json_data: dict[str, object],
        retries: int = 3,
        delay: float = 2.0,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                response = await self._client.post(url, json=json_data)
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

    async def get_term(self, term_id: str) -> dict[str, object] | None:
        """Get a disease term by DOID (e.g. 'DOID:9970')."""
        response = await self._get_with_retry(f"/terms/{term_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def search_terms(self, query: str) -> list[dict[str, object]]:
        """Search disease terms by text."""
        response = await self._post_with_retry(
            "/terms/search",
            json_data={"data": {"names": [query]}},
        )
        if response.status_code != 200:
            return []
        data: object = response.json()
        if isinstance(data, dict):
            results_raw: object = data.get("results", [])
            if isinstance(results_raw, list):
                return [d for d in results_raw if isinstance(d, dict)]
        return []

    async def get_term_by_label(self, label: str) -> dict[str, object] | None:
        """Find a term by its label (e.g. 'breast cancer')."""
        response = await self._get_with_retry(f"/terms/label/{label}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def health_check(self) -> bool:
        try:
            response = await self._get_with_retry("/info")
            return response.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
