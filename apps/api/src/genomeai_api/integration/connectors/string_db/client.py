"""STRING protein-protein interaction REST client."""

from __future__ import annotations

import asyncio
import logging

import httpx

from genomeai_api.integration.connectors.string_db.models import (
    StringEnrichment,
    StringIDMapping,
    StringInteraction,
)

logger = logging.getLogger(__name__)

STRING_BASE_URL = "https://string-db.org/api"


class StringDBClient:
    """Async STRING REST client with retry on transient errors."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=STRING_BASE_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def _get_with_retry(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        retries: int = 3,
        delay: float = 2.0,
    ) -> httpx.Response:
        """GET with retry on transient errors (5xx, timeouts)."""
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
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))
                continue
        raise last_exc  # type: ignore[misc]

    async def get_string_ids(
        self,
        identifiers: list[str],
        species: int = 9606,
        echo_query: bool = True,
    ) -> list[StringIDMapping]:
        """Map gene names to STRING identifiers."""
        joined = "%0d".join(identifiers)
        params: dict[str, str | int] = {
            "identifiers": joined,
            "species": species,
            "echo_query": 1 if echo_query else 0,
            "caller_identity": "genomeai",
        }
        response = await self._get_with_retry("/json/get_string_ids", params=params)
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        mappings: list[StringIDMapping] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                mappings.append(self._parse_id_mapping(typed_item))
        return mappings

    async def get_network(
        self,
        identifiers: list[str],
        species: int = 9606,
        required_score: int = 400,
        network_type: str = "functional",
    ) -> list[StringInteraction]:
        """Get interaction network between input proteins."""
        joined = "%0d".join(identifiers)
        params: dict[str, str | int] = {
            "identifiers": joined,
            "species": species,
            "required_score": required_score,
            "network_type": network_type,
            "caller_identity": "genomeai",
        }
        response = await self._get_with_retry("/json/network", params=params)
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        interactions: list[StringInteraction] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                interactions.append(self._parse_interaction(typed_item))
        return interactions

    async def get_interaction_partners(
        self,
        identifiers: list[str],
        species: int = 9606,
        limit: int = 10,
        required_score: int = 400,
    ) -> list[StringInteraction]:
        """Get top interaction partners for input proteins."""
        joined = "%0d".join(identifiers)
        params: dict[str, str | int] = {
            "identifiers": joined,
            "species": species,
            "limit": limit,
            "required_score": required_score,
            "caller_identity": "genomeai",
        }
        response = await self._get_with_retry("/json/interaction_partners", params=params)
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        interactions: list[StringInteraction] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                interactions.append(self._parse_interaction(typed_item))
        return interactions

    async def get_enrichment(
        self,
        identifiers: list[str],
        species: int = 9606,
    ) -> list[StringEnrichment]:
        """Get functional enrichment for a set of genes."""
        joined = "%0d".join(identifiers)
        params: dict[str, str | int] = {
            "identifiers": joined,
            "species": species,
            "caller_identity": "genomeai",
        }
        response = await self._get_with_retry("/json/enrichment", params=params)
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        enrichments: list[StringEnrichment] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                enrichments.append(self._parse_enrichment(typed_item))
        return enrichments

    async def health_check(self) -> bool:
        """Check if STRING is reachable."""
        try:
            response = await self._get_with_retry(
                "/json/get_string_ids",
                params={"identifiers": "TP53", "species": 9606, "caller_identity": "genomeai"},
            )
            return response.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    def _int_or(self, data: dict[str, object], key: str, default: int) -> int:
        val = data.get(key, default)
        return int(val) if isinstance(val, (int, float)) else default

    def _parse_id_mapping(self, data: dict[str, object]) -> StringIDMapping:
        return StringIDMapping(
            query_item=str(data.get("queryItem", "")),
            string_id=str(data.get("stringId", "")),
            preferred_name=str(data.get("preferredName", "")),
            annotation=str(data.get("annotation", "")),
            ncbi_taxon_id=self._int_or(data, "ncbiTaxonId", 9606),
        )

    def _parse_interaction(self, data: dict[str, object]) -> StringInteraction:
        def _float(key: str) -> float:
            val = data.get(key, 0)
            return float(val) if isinstance(val, (int, float)) else 0.0

        return StringInteraction(
            string_id_a=str(data.get("stringId_A", "")),
            string_id_b=str(data.get("stringId_B", "")),
            preferred_name_a=str(data.get("preferredName_A", "")),
            preferred_name_b=str(data.get("preferredName_B", "")),
            score=_float("score"),
            experimental_score=_float("escore"),
            database_score=_float("dscore"),
            text_mining_score=_float("tscore"),
            ncbi_taxon_id=self._int_or(data, "ncbiTaxonId", 9606),
        )

    def _float_or(self, data: dict[str, object], key: str) -> float:
        val = data.get(key, 0)
        return float(val) if isinstance(val, (int, float)) else 0.0

    def _parse_enrichment(self, data: dict[str, object]) -> StringEnrichment:
        names_raw = data.get("preferredNames", "")
        names_list: list[str] = (
            [n.strip() for n in str(names_raw).split(";") if n.strip()]
            if names_raw
            else []
        )
        return StringEnrichment(
            category=str(data.get("category", "")),
            term=str(data.get("term", "")),
            description=str(data.get("description", "")),
            number_of_genes=self._int_or(data, "number_of_genes", 0),
            p_value=self._float_or(data, "p_value"),
            fdr=self._float_or(data, "fdr"),
            preferred_names=names_list,
        )
