"""AlphaFold connector — predicted protein structures from AlphaFold DB."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.alphafold.models import AlphaFoldStructure

logger = logging.getLogger(__name__)

ALPHAFOLD_API_URL = "https://alphafold.ebi.ac.uk/api"


class AlphaFoldClient:
    """Async AlphaFold DB REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=ALPHAFOLD_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def get_prediction(self, uniprot_id: str) -> AlphaFoldStructure | None:
        """Fetch AlphaFold prediction by UniProt accession."""
        try:
            response = await self._client.get(f"/prediction/{uniprot_id}")
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list) or not data:
                return None
            first = data[0]
            first_typed: dict[str, object] = (
                first if isinstance(first, dict) else {}
            )
            if not first_typed:
                return None
            return self._parse_entry(first_typed)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.warning("AlphaFold fetch error: %s", exc.response.status_code)
            return None

    async def get_prediction_by_gene(
        self, gene: str,
    ) -> AlphaFoldStructure | None:
        """Search UniProt first, then fetch AlphaFold prediction."""
        from genomeai_api.integration.connectors.uniprot.client import UniProtClient
        uniprot = UniProtClient(timeout_seconds=15.0)
        try:
            results = await uniprot.search(gene, max_results=1)
            if not results:
                return None
            return await self.get_prediction(results[0].accession)
        finally:
            await uniprot.close()

    def _parse_entry(self, data: dict[str, object]) -> AlphaFoldStructure:
        entry_id = str(data.get("entryId", ""))
        gene = ""
        genes_raw = data.get("gene", "")
        if isinstance(genes_raw, str):
            gene = genes_raw

        organism_raw = data.get("organismScientificName", "")
        organism = str(organism_raw) if isinstance(organism_raw, str) else ""

        uniprot_raw = data.get("uniprotAccession", "")
        uniprot_id = str(uniprot_raw) if isinstance(uniprot_raw, str) else ""

        raw_seq_len = data.get("uniprotSequence", "")
        seq_len = len(str(raw_seq_len)) if isinstance(raw_seq_len, str) else 0

        pae_img = str(data.get("paeImageUrl", ""))
        cif_url = str(data.get("cifUrl", ""))
        pae_url = str(data.get("paeUrl", ""))
        created = str(data.get("modelCreatedDate", ""))
        conf_ver = str(data.get("latestVersion", ""))

        return AlphaFoldStructure(
            alphafold_id=entry_id,
            gene_name=gene,
            organism=organism,
            uniprot_id=uniprot_id,
            sequence_length=seq_len,
            pae_image_url=pae_img,
            cif_url=cif_url,
            pae_url=pae_url,
            created_date=created,
            confidence_version=conf_ver,
        )

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("/prediction/P00533")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
