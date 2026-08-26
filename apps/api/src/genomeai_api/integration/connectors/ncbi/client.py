"""Core NCBI E-utilities client.

Provides async access to NCBI E-utilities REST API:
- esearch: search databases, get IDs
- efetch: fetch full records by ID
- esummary: fetch summaries by ID
- elink: find related records across databases
- einfo: database metadata

Rate limit: 3 req/s without API key, 10 req/s with free key.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from genomeai_api.integration.connectors.ncbi.models import (
    NCBIGeneRecord,
    NCBISearchResult,
)

logger = logging.getLogger(__name__)

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_RATE_LIMIT_DELAY = 0.35  # ~3 req/s without API key


class NCBIClient:
    """Async NCBI E-utilities client with rate limiting."""

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout_seconds))
        self._last_request_time: float = 0.0

    async def _rate_limit(self) -> None:
        """Enforce NCBI rate limit (3 req/s without key)."""
        now = asyncio.get_running_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < NCBI_RATE_LIMIT_DELAY:
            await asyncio.sleep(NCBI_RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_running_loop().time()

    async def _request(
        self,
        endpoint: str,
        params: dict[str, str | int],
    ) -> httpx.Response:
        """Make rate-limited request to NCBI."""
        await self._rate_limit()
        if self._api_key:
            params["api_key"] = self._api_key
        url = f"{NCBI_BASE_URL}/{endpoint}"
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response

    async def esearch(
        self,
        database: str,
        term: str,
        retmax: int = 20,
        retstart: int = 0,
    ) -> NCBISearchResult:
        """Search NCBI database and return matching IDs.

        Args:
            database: NCBI database (gene, pubmed, nuccore, clinvar, etc.)
            term: Search query using NCBI query syntax
            retmax: Maximum results to return
            retstart: Offset for pagination

        Returns:
            NCBISearchResult with IDs and metadata
        """
        params: dict[str, str | int] = {
            "db": database,
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "retstart": retstart,
        }
        response = await self._request("esearch.fcgi", params)
        text = response.text
        # NCBI sometimes returns JSON with invalid control characters
        import json
        data = json.loads(text, strict=False)
        result = data.get("esearchresult", {})
        return NCBISearchResult(
            database=database,
            count=int(result.get("count", 0)),
            ids=result.get("idlist", []),
            query_translation=result.get("querytranslation", ""),
        )

    async def efetch(
        self,
        database: str,
        ids: list[str],
        rettype: str = "json",
    ) -> Any:
        """Fetch records by IDs from NCBI database.

        Args:
            database: NCBI database name
            ids: List of IDs to fetch
            rettype: Return type (json, xml, text, etc.)

        Returns:
            Parsed response data
        """
        params: dict[str, str | int] = {
            "db": database,
            "id": ",".join(ids),
            "retmode": rettype,
        }
        response = await self._request("efetch.fcgi", params)
        if rettype == "json":
            return response.json()
        return response.text

    async def esummary(
        self,
        database: str,
        ids: list[str],
    ) -> dict[str, Any]:
        """Fetch summaries by IDs from NCBI database.

        Args:
            database: NCBI database name
            ids: List of IDs to fetch

        Returns:
            Dict mapping ID to summary data
        """
        params: dict[str, str | int] = {
            "db": database,
            "id": ",".join(ids),
            "retmode": "json",
        }
        response = await self._request("esummary.fcgi", params)
        data = response.json()
        return data.get("result", {})

    async def elink(
        self,
        source_db: str,
        target_db: str,
        ids: list[str],
    ) -> list[dict[str, str]]:
        """Find linked records between databases.

        Args:
            source_db: Source database
            target_db: Target database
            ids: Source record IDs

        Returns:
            List of {source_id, target_id, target_label} dicts
        """
        params: dict[str, str | int] = {
            "dbfrom": source_db,
            "db": target_db,
            "id": ",".join(ids),
            "retmode": "json",
        }
        response = await self._request("elink.fcgi", params)
        data = response.json()
        links = []
        linksets = data.get("linksets", [])
        for linkset in linksets:
            source_ids = linkset.get("ids", [])
            source_id = source_ids[0] if source_ids else ""
            linksetdbs = linkset.get("linksetdbs", [])
            for db in linksetdbs:
                target_ids = db.get("links", [])
                for target_id in target_ids:
                    links.append(
                        {
                            "source_id": str(source_id),
                            "target_id": str(target_id),
                            "target_db": db.get("dbto", target_db),
                        }
                    )
        return links

    async def einfo(self, database: str | None = None) -> dict[str, Any]:
        """Get database metadata.

        Args:
            database: Optional specific database, or None for list of all databases

        Returns:
            Database metadata dict
        """
        params: dict[str, str | int] = {"retmode": "json"}
        if database:
            params["db"] = database
        response = await self._request("einfo.fcgi", params)
        return response.json()

    def _parse_gene_xml(self, xml_text: str) -> list[NCBIGeneRecord]:
        """Parse gene XML response into NCBIGeneRecord objects."""
        records = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            logger.warning("Failed to parse NCBI gene XML")
            return records

        for gene_elem in root.findall(".//Entrezgene"):
            gene_id_elem = gene_elem.find(".//Gene-track_geneid")
            gene_id = gene_id_elem.text if gene_id_elem is not None else ""

            symbol_elem = gene_elem.find(".//Gene-ref_locus")
            symbol = symbol_elem.text if symbol_elem is not None else ""

            name_elem = gene_elem.find(".//Gene-ref_desc")
            name = name_elem.text if name_elem is not None else ""

            org_elem = gene_elem.find(".//Org-ref_taxname")
            organism = "Homo sapiens"
            if org_elem is not None and org_elem.text:
                organism = org_elem.text

            # Chromosome from BioSource subtype
            chrom = ""
            for subsource in gene_elem.findall(".//SubSource"):
                subtype = subsource.find("SubSource_subtype")
                if subtype is not None and subtype.get("value") == "chromosome":
                    name_elem2 = subsource.find("SubSource_name")
                    if name_elem2 is not None and name_elem2.text:
                        chrom = name_elem2.text
                    break

            # Map location from Gene-ref_maploc
            map_loc_elem = gene_elem.find(".//Gene-ref_maploc")
            map_location = map_loc_elem.text if map_loc_elem is not None else ""

            aliases: list[str] = []
            for alias_elem in gene_elem.findall(".//Gene-ref_syn_E"):
                if alias_elem.text:
                    aliases.append(alias_elem.text)

            # Gene type from Entrezgene_type
            gene_type_elem = gene_elem.find(".//Entrezgene_type")
            gene_type = gene_type_elem.get("value", "") if gene_type_elem is not None else ""

            if gene_id and symbol:
                records.append(
                    NCBIGeneRecord(
                        gene_id=gene_id,
                        symbol=symbol,
                        name=name or "",
                        organism=organism,
                        chromosome=chrom,
                        map_location=map_location or f"{chrom}q",
                        description=name or "",
                        aliases=aliases,
                        gene_type=gene_type,
                    )
                )
        return records

    async def search_genes(
        self,
        query: str,
        organism: str = "Homo sapiens",
        max_results: int = 20,
    ) -> list[NCBIGeneRecord]:
        """Search for genes by name/symbol and fetch full records.

        Args:
            query: Gene name or symbol (e.g., "BRCA1")
            organism: Organism name
            max_results: Maximum genes to return

        Returns:
            List of NCBIGeneRecord objects
        """
        search_term = f"{query}[Gene Name] AND {organism}[Organism]"
        result = await self.esearch("gene", search_term, retmax=max_results)

        if not result.ids:
            return []

        xml_text = await self.efetch("gene", result.ids, rettype="xml")
        return self._parse_gene_xml(xml_text)

    async def get_gene(self, gene_id: str) -> NCBIGeneRecord | None:
        """Fetch a single gene by NCBI Gene ID.

        Args:
            gene_id: NCBI Gene ID (e.g., "672" for BRCA1)

        Returns:
            NCBIGeneRecord or None if not found
        """
        xml_text = await self.efetch("gene", [gene_id], rettype="xml")
        records = self._parse_gene_xml(xml_text)
        return records[0] if records else None

    async def health_check(self) -> bool:
        """Check if NCBI E-utilities is reachable."""
        try:
            await self.einfo("gene")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
