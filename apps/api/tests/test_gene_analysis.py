"""Tests for gene analysis engine — REAL NCBI + REAL Ollama.

These tests use real NCBI API calls and real Ollama inference.
If Ollama is not running, AI analysis tests are skipped but basic analysis still works.
"""

import pytest

from genomeai_api.ai.ollama import OllamaProvider
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.services.gene_analysis import GeneAnalysisEngine


@pytest.fixture
def engine() -> GeneAnalysisEngine:
    return GeneAnalysisEngine(
        ai_provider=OllamaProvider(),
        ncbi_client=NCBIClient(),
    )


class TestGeneAnalysisEngine:
    """Tests for gene analysis with REAL data."""

    @pytest.mark.asyncio
    async def test_analyze_brca1(self, engine: GeneAnalysisEngine) -> None:
        """Analyze BRCA1 gene — verify returns structured analysis."""
        analysis = await engine.analyze_by_symbol("BRCA1")
        assert analysis.gene_symbol == "BRCA1"
        assert analysis.gene_id == "672"
        assert analysis.name
        assert analysis.organism == "Homo sapiens"
        assert analysis.source in ("ncbi", "ncbi+ollama")

    @pytest.mark.asyncio
    async def test_analyze_tp53(self, engine: GeneAnalysisEngine) -> None:
        """Analyze TP53 gene — verify returns structured analysis."""
        analysis = await engine.analyze_by_symbol("TP53")
        assert analysis.gene_symbol == "TP53"
        assert analysis.gene_id == "7157"
        assert analysis.name

    @pytest.mark.asyncio
    async def test_analyze_by_id(self, engine: GeneAnalysisEngine) -> None:
        """Analyze BRCA1 by Gene ID 672 — verify returns correct gene."""
        analysis = await engine.analyze_by_id("672")
        assert analysis.gene_symbol == "BRCA1"
        assert analysis.gene_id == "672"

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_gene(self, engine: GeneAnalysisEngine) -> None:
        """Analyze nonexistent gene — verify raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await engine.analyze_by_symbol("XYZNONEXISTENT123")

    @pytest.mark.asyncio
    async def test_basic_analysis_without_ai(self) -> None:
        """Test basic analysis without AI (fallback mode)."""
        from genomeai_api.integration.connectors.ncbi.models import NCBIGeneRecord

        record = NCBIGeneRecord(
            gene_id="672",
            symbol="BRCA1",
            name="BRCA1 DNA repair associated",
            organism="Homo sapiens",
            chromosome="17",
            map_location="17q21.31",
        )
        engine = GeneAnalysisEngine(
            ai_provider=OllamaProvider(),
            ncbi_client=NCBIClient(),
        )
        analysis = await engine.analyze_from_record(record)
        assert analysis.gene_symbol == "BRCA1"
        assert analysis.gene_id == "672"
        assert analysis.source == "ncbi"
