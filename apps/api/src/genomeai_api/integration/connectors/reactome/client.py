"""Reactome Content Service REST client."""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from genomeai_api.integration.connectors.reactome.models import (
    ReactomeParticipant,
    ReactomePathway,
    ReactomeSearchResult,
)

logger = logging.getLogger(__name__)

REACTOME_BASE_URL = "https://reactome.org/ContentService"


class ReactomeClient:
    """Async Reactome REST client with retry on transient errors."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=REACTOME_BASE_URL,
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

    async def search_pathways(
        self,
        query: str,
        species: str = "Human",
        max_results: int = 10,
    ) -> ReactomeSearchResult:
        """Search Reactome for pathways matching a gene or term."""
        params: dict[str, str | int] = {
            "query": query,
            "species": species,
            "types": "Pathway",
            "rows": max_results,
        }
        response = await self._get_with_retry("/search/query", params=params)
        response.raise_for_status()
        data: dict[str, object] = response.json()

        raw_count = data.get("numberOfMatches", 0)
        total = int(raw_count) if isinstance(raw_count, (int, float)) else 0
        pathways: list[ReactomePathway] = []

        results_raw = data.get("results", [])
        results_list: list[object] = results_raw if isinstance(results_raw, list) else []
        for group in results_list:
            if not isinstance(group, dict):
                continue
            entries_raw = group.get("entries", [])
            entries: list[object] = entries_raw if isinstance(entries_raw, list) else []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                typed_entry: dict[str, object] = entry
                pathways.append(self._parse_pathway(typed_entry))

        return ReactomeSearchResult(total_matches=total, pathways=pathways)

    async def get_pathway_detail(self, st_id: str) -> dict[str, object] | None:
        """Get full pathway detail by Reactome Standard ID."""
        response = await self._get_with_retry(f"/data/query/{st_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def get_pathway_participants(self, db_id: int) -> list[ReactomeParticipant]:
        """Get participant entities of a pathway by numeric dbId."""
        response = await self._get_with_retry(f"/data/participants/{db_id}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        participants: list[ReactomeParticipant] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                participants.append(self._parse_participant(typed_item))
        return participants

    async def get_pathways_for_entity(
        self,
        st_id: str,
        tax_id: str = "9606",
    ) -> list[ReactomePathway]:
        """Get pathways containing a given entity (by its Standard ID)."""
        response = await self._get_with_retry(
            f"/data/pathways/low/diagram/entity/{st_id}",
            params={"species": tax_id},
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        raw: list[object] = response.json() if isinstance(response.json(), list) else []
        pathways: list[ReactomePathway] = []
        for item in raw:
            if isinstance(item, dict):
                typed_item: dict[str, object] = item
                pathways.append(self._parse_pathway(typed_item))
        return pathways

    async def health_check(self) -> bool:
        """Check if Reactome Content Service is reachable."""
        try:
            response = await self._client.get("/data/pathways/top/9606")
            return response.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags from Reactome response text."""
        return re.sub(r"<[^>]+>", "", text)

    @staticmethod
    def _to_str(val: object) -> str:
        """Convert a JSON value to string, handling list wrapping."""
        if isinstance(val, str):
            return val
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, list):
            if val:
                return str(val[0])  # pyright: ignore[reportUnknownArgumentType]
            return ""
        return ""

    def _parse_pathway(self, data: dict[str, object]) -> ReactomePathway:
        db_id_raw = data.get("dbId", 0)
        if isinstance(db_id_raw, str):
            db_id = int(db_id_raw) if db_id_raw.isdigit() else 0
        elif isinstance(db_id_raw, (int, float)):
            db_id = int(db_id_raw)
        else:
            db_id = 0

        st_id = str(data.get("stId", ""))
        name = self._strip_html(self._to_str(data.get("displayName", data.get("name", ""))))
        species = self._to_str(data.get("speciesName", data.get("species", "Homo sapiens")))

        schema_class = str(data.get("schemaClass", "Pathway"))

        compartment_raw = data.get("compartmentNames", [])
        compartments: list[str] = (
            [str(c) for c in compartment_raw if isinstance(c, str)]
            if isinstance(compartment_raw, list)
            else []
        )

        return ReactomePathway(
            db_id=db_id,
            st_id=st_id,
            name=name,
            species=species,
            schema_class=schema_class,
            compartment_names=compartments,
        )

    def _parse_participant(self, data: dict[str, object]) -> ReactomeParticipant:
        db_id_raw = data.get("peDbId", data.get("dbId", 0))
        db_id = int(db_id_raw) if isinstance(db_id_raw, (int, float)) else 0
        display_name = str(data.get("displayName", ""))
        schema_class = str(data.get("schemaClass", ""))

        ref_identifiers: list[str] = []
        ref_names: list[str] = []
        ref_entities_raw = data.get("refEntities", [])
        ref_entities: list[object] = ref_entities_raw if isinstance(ref_entities_raw, list) else []
        for ref in ref_entities:
            if not isinstance(ref, dict):
                continue
            typed_ref: dict[str, object] = ref
            identifier = str(typed_ref.get("identifier", ""))
            if identifier:
                ref_identifiers.append(identifier)
            dn = str(typed_ref.get("displayName", ""))
            if dn:
                ref_names.append(dn)

        return ReactomeParticipant(
            db_id=db_id,
            display_name=display_name,
            schema_class=schema_class,
            ref_identifiers=ref_identifiers,
            ref_names=ref_names,
        )
