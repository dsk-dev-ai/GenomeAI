"""Tests for NCBI E-utilities connector — REAL API calls, no mocks.

These tests hit the actual NCBI E-utilities API to verify the connector works.
Rate limit: 3 req/s (enforced by client).
"""

import pytest
from genomeai_api.integration.connectors.base import DataSourceConfig
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.integration.connectors.ncbi.gene import (
    NCBIGeneConnector,
    NCBIGeneFetchRequest,
    NCBIGeneSearchRequest,
)


@pytest.fixture
def client() -> NCBIClient:
    return NCBIClient()


@pytest.fixture
def gene_connector() -> NCBIGeneConnector:
    config = DataSourceConfig(
        source_id="ncbi-gene",
        api_base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
    )
    return NCBIGeneConnector(config)


class TestNCBIClient:
    """Tests for the core NCBI client with REAL API calls."""

    @pytest.mark.asyncio
    async def test_esearch_brca1(self, client: NCBIClient) -> None:
        """Search for BRCA1 in gene database — verify returns Gene ID 672."""
        result = await client.esearch(
            database="gene",
            term="BRCA1[Gene Name] AND Homo sapiens[Organism]",
            retmax=5,
        )
        assert result.count >= 1
        assert "672" in result.ids
        assert result.database == "gene"

    @pytest.mark.asyncio
    async def test_esearch_tp53(self, client: NCBIClient) -> None:
        """Search for TP53 in gene database — verify returns Gene ID 7157."""
        result = await client.esearch(
            database="gene",
            term="TP53[Gene Name] AND Homo sapiens[Organism]",
            retmax=5,
        )
        assert result.count >= 1
        assert "7157" in result.ids

    @pytest.mark.asyncio
    async def test_efetch_gene_672(self, client: NCBIClient) -> None:
        """Fetch BRCA1 gene record by ID 672 — verify returns gene data."""
        records = await client.search_genes("BRCA1", max_results=1)
        assert len(records) >= 1
        record = records[0]
        assert record.gene_id == "672"
        assert record.symbol == "BRCA1"
        assert "breast" in record.name.lower() or "BRCA1" in record.name
        assert record.organism == "Homo sapiens"

    @pytest.mark.asyncio
    async def test_efetch_gene_7157(self, client: NCBIClient) -> None:
        """Fetch TP53 gene record by ID 7157 — verify returns gene data."""
        record = await client.get_gene("7157")
        assert record is not None
        assert record.gene_id == "7157"
        assert record.symbol == "TP53"
        assert record.organism == "Homo sapiens"

    @pytest.mark.asyncio
    async def test_einfo_gene_database(self, client: NCBIClient) -> None:
        """Get gene database metadata — verify returns field list."""
        info = await client.einfo("gene")
        assert "einforesult" in info
        result = info["einforesult"]
        dbinfo = result["dbinfo"]
        assert isinstance(dbinfo, list)
        assert len(dbinfo) > 0
        assert dbinfo[0]["dbname"] == "gene"

    @pytest.mark.asyncio
    async def test_elink_gene_to_pubmed(self, client: NCBIClient) -> None:
        """Find PubMed articles linked to BRCA1 gene — verify returns links."""
        links = await client.elink(
            source_db="gene",
            target_db="pubmed",
            ids=["672"],
        )
        assert len(links) > 0
        assert links[0]["source_id"] == "672"

    @pytest.mark.asyncio
    async def test_health_check(self, client: NCBIClient) -> None:
        """Health check — verify NCBI is reachable."""
        ok = await client.health_check()
        assert ok is True

    @pytest.mark.asyncio
    async def test_search_egfr(self, client: NCBIClient) -> None:
        """Search for EGFR gene — verify returns results."""
        records = await client.search_genes("EGFR", max_results=3)
        assert len(records) >= 1
        symbols = [r.symbol for r in records]
        assert "EGFR" in symbols


class TestNCBIGeneConnector:
    """Tests for the gene connector with REAL API calls."""

    @pytest.mark.asyncio
    async def test_search_request(self, gene_connector: NCBIGeneConnector) -> None:
        """Search genes via connector — verify returns real results."""
        request = NCBIGeneSearchRequest(query="BRCA1", max_results=3)
        results = await gene_connector.fetch(request)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert results[0].symbol == "BRCA1"

    @pytest.mark.asyncio
    async def test_fetch_request(self, gene_connector: NCBIGeneConnector) -> None:
        """Fetch single gene via connector — verify returns real record."""
        request = NCBIGeneFetchRequest(gene_id="672")
        results = await gene_connector.fetch(request)
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].gene_id == "672"
        assert results[0].symbol == "BRCA1"

    @pytest.mark.asyncio
    async def test_health(self, gene_connector: NCBIGeneConnector) -> None:
        """Health check via connector — verify NCBI reachable."""
        health = await gene_connector.health_check()
        assert health.ok is True
        assert health.source_id == "ncbi-gene"
