"""Gene-specific NCBI connector — search and fetch gene records.

Wraps the core NCBIClient with gene-specific logic.
"""

from __future__ import annotations

import logging

from genomeai_api.integration.connectors.base import (
    ConnectorHealth,
    DataSourceConfig,
    DataSourceConnector,
    DataSourceDefinition,
)
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.integration.types import AccessMode, AuthMode, SourceType

logger = logging.getLogger(__name__)

NCBI_GENE_DEFINITION = DataSourceDefinition(
    source_id="ncbi-gene",
    provider="ncbi",
    display_name="NCBI Gene",
    source_type=SourceType.GENE,
    documentation_url="https://www.ncbi.nlm.nih.gov/books/NBK3800/",
    access_mode=AccessMode.LIVE,
    authentication_mode=AuthMode.NONE,
    license_info={
        "name": "Public Domain",
        "url": "https://www.ncbi.nlm.nih.gov/about/policies/",
    },
    description="NCBI E-utilities gene database — 38 biomedical databases",
)


class NCBIGeneConnector(DataSourceConnector):
    """NCBI Gene connector — fetch gene records from NCBI E-utilities."""

    definition = NCBI_GENE_DEFINITION

    def __init__(self, config: DataSourceConfig) -> None:
        super().__init__(config)
        api_key = config.feature_flags.get("api_key") or config.credential_ref
        self._client = NCBIClient(
            api_key=str(api_key) if api_key else None,
            timeout_seconds=config.request_timeout_seconds,
        )

    @property
    def current_version(self) -> str | None:
        return "2026.08"

    async def health_check(self) -> ConnectorHealth:
        """Verify NCBI E-utilities is reachable."""
        ok = await self._client.health_check()
        return ConnectorHealth(
            source_id=self.config.source_id,
            ok=ok,
            message="NCBI E-utilities reachable" if ok else "NCBI E-utilities unreachable",
        )

    async def fetch(self, request: object) -> object:
        """Fetch gene data from NCBI.

        Args:
            request: NCBIGeneSearchRequest or NCBIGeneFetchRequest

        Returns:
            List of NCBIGeneRecord objects
        """
        from genomeai_api.integration.connectors.ncbi.models import (
            NCBIRefLinkRecord,
        )

        if isinstance(request, NCBIGeneSearchRequest):
            return await self._client.search_genes(
                query=request.query,
                organism=request.organism,
                max_results=request.max_results,
            )
        if isinstance(request, NCBIGeneFetchRequest):
            record = await self._client.get_gene(request.gene_id)
            return [record] if record else []
        if isinstance(request, NCBIGeneLinkRequest):
            links = await self._client.elink(
                source_db=request.source_db,
                target_db=request.target_db,
                ids=request.ids,
            )
            return [
                NCBIRefLinkRecord(
                    source_db=request.source_db,
                    source_id=link["source_id"],
                    target_db=link["target_db"],
                    target_id=link["target_id"],
                )
                for link in links
            ]
        raise ValueError(f"Unknown request type: {type(request)}")

    async def close(self) -> None:
        """Close the NCBI client."""
        await self._client.close()


class NCBIGeneSearchRequest:
    """Request to search NCBI gene database."""

    def __init__(
        self,
        query: str,
        organism: str = "Homo sapiens",
        max_results: int = 20,
    ) -> None:
        self.query = query
        self.organism = organism
        self.max_results = max_results


class NCBIGeneFetchRequest:
    """Request to fetch a specific gene by ID."""

    def __init__(self, gene_id: str) -> None:
        self.gene_id = gene_id


class NCBIGeneLinkRequest:
    """Request to find linked records across databases."""

    def __init__(
        self,
        source_db: str,
        target_db: str,
        ids: list[str],
    ) -> None:
        self.source_db = source_db
        self.target_db = target_db
        self.ids = ids
