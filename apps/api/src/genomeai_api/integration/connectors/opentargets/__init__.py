"""OpenTargets Platform GraphQL client."""

from __future__ import annotations

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

OPENTARGETS_BASE_URL = "https://api.platform.opentargets.org/api/v4/graphql"


class OpenTargetsClient:
    """Async OpenTargets GraphQL client with retry."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"Content-Type": "application/json"},
        )
        self._url = OPENTARGETS_BASE_URL

    async def _post_with_retry(
        self,
        json_data: dict[str, object],
        retries: int = 3,
        delay: float = 2.0,
    ) -> dict[str, object]:
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                response = await self._client.post(self._url, json=json_data)
                if response.status_code >= 500:
                    last_exc = httpx.HTTPStatusError(
                        f"Server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    continue
                response.raise_for_status()
                data: dict[str, object] = response.json()
                return data
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = exc
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    async def search_disease(self, query: str, size: int = 5) -> list[dict[str, object]]:
        """Search for diseases by name."""
        graphql_query = """
        query Search($query: String!, $size: Int!) {
            search(queryString: $query, entityNames: ["disease"], page: {index: 0, size: $size}) {
                total
                hits {
                    id
                    name
                    entity
                    description
                }
            }
        }
        """
        data = await self._post_with_retry({
            "query": graphql_query,
            "variables": {"query": query, "size": size},
        })
        search_data = data.get("data", {})
        if isinstance(search_data, dict):
            search_obj = search_data.get("search", {})
            if isinstance(search_obj, dict):
                hits_raw = search_obj.get("hits", [])
                if isinstance(hits_raw, list):
                    return [h for h in hits_raw if isinstance(h, dict)]
        return []

    async def get_disease_associations(
        self,
        disease_id: str,
        size: int = 10,
    ) -> dict[str, object]:
        """Get gene-disease associations for a disease."""
        graphql_query = """
        query DiseaseAssociations($diseaseId: String!, $size: Int!) {
            disease(ontologyId: $diseaseId) {
                id
                name
                description
                knownDrugs(size: $size) {
                    uniqueDrugs
                    rows {
                        drug { id name }
                        phase
                    }
                }
                associatedTargets(page: {index: 0, size: $size}) {
                    count
                    rows {
                        target {
                            id
                            approvedSymbol
                            approvedName
                        }
                        score
                    }
                }
            }
        }
        """
        data = await self._post_with_retry({
            "query": graphql_query,
            "variables": {"diseaseId": disease_id, "size": size},
        })
        result: dict[str, object] = {}
        data_obj = data.get("data", {})
        if isinstance(data_obj, dict):
            disease = data_obj.get("disease")
            if isinstance(disease, dict):
                result = disease
        return result

    async def get_target_diseases(
        self,
        target_id: str,
        size: int = 10,
    ) -> dict[str, object]:
        """Get diseases associated with a gene/target."""
        graphql_query = """
        query TargetDiseases($targetId: String!, $size: Int!) {
            target(ensemblId: $targetId) {
                id
                approvedSymbol
                approvedName
                associatedDiseases(page: {index: 0, size: $size}) {
                    count
                    rows {
                        disease {
                            id
                            name
                            description
                        }
                        score
                    }
                }
            }
        }
        """
        data = await self._post_with_retry({
            "query": graphql_query,
            "variables": {"targetId": target_id, "size": size},
        })
        result: dict[str, object] = {}
        data_obj = data.get("data", {})
        if isinstance(data_obj, dict):
            target = data_obj.get("target")
            if isinstance(target, dict):
                result = target
        return result

    async def resolve_gene_to_ensembl(self, gene_symbol: str) -> str | None:
        """Resolve a gene symbol to an Ensembl ID via OpenTargets search."""
        graphql_query = """
        query Search($query: String!) {
            search(queryString: $query, entityNames: ["target"], page: {index: 0, size: 3}) {
                hits {
                    id
                    name
                    entity
                }
            }
        }
        """
        data = await self._post_with_retry({
            "query": graphql_query,
            "variables": {"query": gene_symbol},
        })
        search_data = data.get("data", {})
        if isinstance(search_data, dict):
            search_obj = search_data.get("search", {})
            if isinstance(search_obj, dict):
                hits_raw = search_obj.get("hits", [])
                if isinstance(hits_raw, list):
                    for hit in hits_raw:
                        if isinstance(hit, dict):
                            name_val: object = hit.get("name", "")
                            id_val: object = hit.get("id", "")
                            # pyright: ignore[reportUnknownArgumentType]
                            name_upper = name_val.upper() if isinstance(name_val, str) else ""
                            symbol_upper = gene_symbol.upper()
                            if name_upper == symbol_upper:
                                return str(id_val)  # pyright: ignore[reportUnknownArgumentType]
                    if hits_raw and isinstance(hits_raw[0], dict):
                        first_id: object = hits_raw[0].get("id", "")
                        return str(first_id)  # pyright: ignore[reportUnknownArgumentType]
        return None

    async def health_check(self) -> bool:
        try:
            data = await self._post_with_retry({
                "query": "{ __typename }",
                "variables": {},
            })
            return bool(data)
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
