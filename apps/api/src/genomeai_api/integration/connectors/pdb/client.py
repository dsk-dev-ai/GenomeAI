"""PDB connector — protein 3D structures via RCSB REST API."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.pdb.models import PDBStructure

logger = logging.getLogger(__name__)

RCSB_REST_URL = "https://data.rcsb.org/rest/v1"


class PDBClient:
    """Async RCSB PDB REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=RCSB_REST_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def get_structure(self, pdb_id: str) -> PDBStructure | None:
        """Fetch a single PDB structure by ID."""
        try:
            response = await self._client.get(f"/core/entry/{pdb_id.upper()}")
            response.raise_for_status()
            data: dict[str, object] = response.json()
            return self._parse_entry(data)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("PDB fetch error: %s", exc.response.status_code)
            return None

    async def search_by_gene(
        self, gene: str, max_results: int = 5,
    ) -> list[PDBStructure]:
        """Search PDB for structures by keyword (gene/protein name)."""
        try:
            search_url = "https://search.rcsb.org/rcsbsearch/v2/query"
            payload: dict[str, object] = {
                "query": {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "struct_keywords.pdbx_keywords_text",
                        "operator": "contains_words",
                        "value": gene,
                    },
                },
                "return_type": "entry",
                "request_options": {
                    "paginate": {"start": 0, "rows": max_results},
                    "results_content_type": ["experimental"],
                },
            }
            response = await self._client.post(
                search_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            result_set = data.get("result_set", [])
            results: list[PDBStructure] = []
            if isinstance(result_set, list):
                for item in result_set[:max_results]:
                    if not isinstance(item, dict):
                        continue
                    identifier = item.get("identifier", "")
                    pdb_id = str(identifier) if isinstance(identifier, str) else ""
                    if pdb_id:
                        struct = await self.get_structure(pdb_id)
                        if struct:
                            results.append(struct)
            return results
        except Exception as exc:
            logger.warning("PDB search error: %s", exc)
            return []

    def _parse_entry(self, data: dict[str, object]) -> PDBStructure:
        struct = data.get("struct", {})
        struct_dict: dict[str, object] = (
            struct if isinstance(struct, dict) else {}
        )
        title = str(struct_dict.get("title", ""))

        exptl = data.get("exptl", [])
        method = ""
        if isinstance(exptl, list) and exptl:
            first_item: dict[str, object] = (
                exptl[0] if isinstance(exptl[0], dict) else {}
            )
            if first_item:
                raw_method = first_item.get("method", "")
                method = str(raw_method) if isinstance(raw_method, str) else ""

        refine = data.get("refine", [])
        resolution = 0.0
        if isinstance(refine, list) and refine:
            first_ref: dict[str, object] = (
                refine[0] if isinstance(refine[0], dict) else {}
            )
            if first_ref:
                res = first_ref.get("ls_d_res_high")
                if isinstance(res, (int, float)):
                    resolution = float(res)

        src_organism = data.get("rcsb_entry_container_identifiers", {})
        src_dict: dict[str, object] = (
            src_organism if isinstance(src_organism, dict) else {}
        )
        organism = str(src_dict.get("organism_name", "")) if src_dict.get("organism_name") else ""

        pdb_id_raw = data.get("rcsb_id", "")
        pdb_id = str(pdb_id_raw) if isinstance(pdb_id_raw, str) else ""

        cell = data.get("cell", {})
        cell_dict: dict[str, object] = (
            cell if isinstance(cell, dict) else {}
        )
        chain_count_raw = cell_dict.get("Z", 0)
        chain_count = int(chain_count_raw) if isinstance(chain_count_raw, (int, float)) else 0

        return PDBStructure(
            pdb_id=pdb_id,
            title=title,
            method=method,
            resolution=resolution,
            organism=organism,
            chain_count=chain_count,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/core/entry/4HHB")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
