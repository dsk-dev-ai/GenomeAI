"""Tests for variant connectors — REAL API calls, no mocks."""

import pytest
from genomeai_api.integration.connectors.clinvar.client import ClinVarClient
from genomeai_api.integration.connectors.ensembl_vep.client import EnsemblVEPClient
from genomeai_api.integration.connectors.gnomad.client import GnomADClient


@pytest.fixture
def clinvar() -> ClinVarClient:
    return ClinVarClient()


@pytest.fixture
def gnomad() -> GnomADClient:
    return GnomADClient()


@pytest.fixture
def vep() -> EnsemblVEPClient:
    return EnsemblVEPClient()


class TestClinVar:
    @pytest.mark.asyncio
    async def test_search_brca1_pathogenic(self, clinvar: ClinVarClient) -> None:
        records = await clinvar.search_variants("BRCA1", significance="pathogenic", max_results=5)
        assert len(records) > 0
        assert any(r.gene_symbol == "BRCA1" for r in records)

    @pytest.mark.asyncio
    async def test_search_tp53(self, clinvar: ClinVarClient) -> None:
        records = await clinvar.search_variants("TP53", max_results=3)
        assert len(records) > 0

    @pytest.mark.asyncio
    async def test_health(self, clinvar: ClinVarClient) -> None:
        assert await clinvar.health_check()


class TestGnomAD:
    @pytest.mark.asyncio
    async def test_known_variant(self, gnomad: GnomADClient) -> None:
        variant = await gnomad.get_variant("19-44908822-C-T")
        assert variant is not None
        assert variant.genome_af > 0

    @pytest.mark.asyncio
    async def test_nonexistent_variant(self, gnomad: GnomADClient) -> None:
        variant = await gnomad.get_variant("1-99999999-G-A")
        assert variant is None

    @pytest.mark.asyncio
    async def test_health(self, gnomad: GnomADClient) -> None:
        assert await gnomad.health_check()


class TestEnsemblVEP:
    @pytest.mark.asyncio
    async def test_brca2_missense(self, vep: EnsemblVEPClient) -> None:
        result = await vep.predict_hgvs("ENST00000380152.8:c.5426G>A")
        assert result is not None
        assert len(result.consequences) > 0
        assert "missense_variant" in result.consequences[0].consequence_terms

    @pytest.mark.asyncio
    async def test_health(self, vep: EnsemblVEPClient) -> None:
        assert await vep.health_check()
