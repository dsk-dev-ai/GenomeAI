"""KEGG REST client (plain text API)."""

from __future__ import annotations

import asyncio
import logging
import re

import httpx

from genomeai_api.integration.connectors.kegg.models import (
    KEGGPathway,
    KEGGPathwayDetail,
)

logger = logging.getLogger(__name__)

KEGG_BASE_URL = "https://rest.kegg.jp"


class KEGGClient:
    """Async KEGG REST client with retry on transient errors."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=KEGG_BASE_URL,
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

    async def list_pathways(self, organism: str = "hsa") -> list[KEGGPathway]:
        """List all pathways for an organism (default: human)."""
        response = await self._get_with_retry(f"/list/pathway/{organism}")
        response.raise_for_status()
        text = response.text
        pathways: list[KEGGPathway] = []
        for line in text.strip().splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                pid = parts[0].strip()
                # Strip " - Organism name" suffix
                name = re.sub(r"\s*-\s+.*$", "", parts[1].strip())
                pathways.append(KEGGPathway(pathway_id=pid, name=name, organism=organism))
        return pathways

    async def get_pathway_detail(self, pathway_id: str) -> KEGGPathwayDetail | None:
        """Get pathway detail by KEGG ID (e.g. 'hsa04115')."""
        response = await self._get_with_retry(f"/get/{pathway_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._parse_flat_file(pathway_id, response.text)

    async def find_genes(
        self,
        organism: str,
        query: str,
    ) -> list[str]:
        """Find genes matching a keyword in an organism database."""
        response = await self._get_with_retry(f"/find/{organism}/{query}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        gene_ids: list[str] = []
        for line in response.text.strip().splitlines():
            parts = line.split("\t", 1)
            if parts:
                gene_ids.append(parts[0].strip())
        return gene_ids

    async def get_pathways_for_gene(self, gene_entry: str) -> list[KEGGPathway]:
        """Get all pathways containing a gene (e.g. 'hsa:672' for BRCA1)."""
        response = await self._get_with_retry(f"/link/pathway/{gene_entry}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        pathways: list[KEGGPathway] = []
        for line in response.text.strip().splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                pid = parts[1].strip().replace("path:", "")
                # Extract name from pathway list if available
                pathways.append(KEGGPathway(pathway_id=pid, name=""))
        return pathways

    async def get_genes_in_pathway(self, pathway_id: str) -> list[str]:
        """Get all genes in a pathway (e.g. 'hsa04115')."""
        response = await self._get_with_retry(f"/link/hsa/{pathway_id}")
        if response.status_code == 404:
            return []
        response.raise_for_status()
        gene_ids: list[str] = []
        for line in response.text.strip().splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                gene_ids.append(parts[1].strip())
        return gene_ids

    async def health_check(self) -> bool:
        """Check if KEGG is reachable."""
        try:
            response = await self._get_with_retry("/list/pathway/hsa", params={})
            return response.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()

    def _parse_flat_file(self, pathway_id: str, text: str) -> KEGGPathwayDetail:
        """Parse KEGG flat-file format response."""
        name = ""
        description = ""
        organism = ""
        genes: list[str] = []
        classes: list[str] = []
        references: list[str] = []

        current_field = ""

        for line in text.splitlines():
            # Field lines start at column 0 with a word, then 12 spaces for data
            match = re.match(r"^(\w[\w_-]*)\s{2,}(.*)$", line)
            if match:
                current_field = match.group(1)
                value = match.group(2).strip()
                if current_field == "NAME":
                    name = value
                elif current_field == "DESCRIPTION":
                    description = value
                elif current_field == "ORGANISM":
                    organism = value
                elif current_field == "CLASS":
                    classes.append(value)
                elif current_field == "GENE":
                    # Gene lines: "  672  BRCA1; ..."
                    gene_match = re.match(r"^\s+(\d+)\s+(\S+)", value)
                    if gene_match:
                        genes.append(gene_match.group(2).rstrip(";"))
                elif current_field == "REFERENCE":
                    ref_match = re.search(r"PMID:(\d+)", value)
                    if ref_match:
                        references.append(ref_match.group(1))
            elif line.startswith(" ") and current_field:
                # Continuation line
                if current_field == "GENE":
                    gene_match = re.match(r"^\s+(\d+)\s+(\S+)", line)
                    if gene_match:
                        genes.append(gene_match.group(2).rstrip(";"))
                elif current_field == "CLASS":
                    classes.append(line.strip())

        return KEGGPathwayDetail(
            pathway_id=pathway_id,
            name=name,
            description=description,
            organism=organism,
            genes=genes,
            classes=classes,
            references=references,
        )
