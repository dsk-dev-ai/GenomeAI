"""Tests for protein connectors — REAL API calls, no mocks."""

import pytest
from genomeai_api.integration.connectors.alphafold.client import AlphaFoldClient
from genomeai_api.integration.connectors.pdb.client import PDBClient
from genomeai_api.integration.connectors.uniprot.client import UniProtClient


@pytest.fixture
def uniprot() -> UniProtClient:
    return UniProtClient()


@pytest.fixture
def pdb() -> PDBClient:
    return PDBClient()


@pytest.fixture
def alphafold() -> AlphaFoldClient:
    return AlphaFoldClient()


class TestUniProt:
    @pytest.mark.asyncio
    async def test_search_brca1(self, uniprot: UniProtClient) -> None:
        proteins = await uniprot.search("BRCA1", max_results=3)
        assert len(proteins) > 0
        assert any("BRCA1" in p.gene_names for p in proteins)

    @pytest.mark.asyncio
    async def test_get_by_accession(self, uniprot: UniProtClient) -> None:
        protein = await uniprot.get_protein("P38398")
        assert protein is not None
        assert protein.accession == "P38398"
        assert protein.length > 0

    @pytest.mark.asyncio
    async def test_health(self, uniprot: UniProtClient) -> None:
        assert await uniprot.health_check()


class TestPDB:
    @pytest.mark.asyncio
    async def test_get_structure(self, pdb: PDBClient) -> None:
        struct = await pdb.get_structure("1JM7")
        assert struct is not None
        assert struct.pdb_id == "1JM7"
        assert struct.method != ""

    @pytest.mark.asyncio
    async def test_health(self, pdb: PDBClient) -> None:
        assert await pdb.health_check()


class TestAlphaFold:
    @pytest.mark.asyncio
    async def test_get_prediction(self, alphafold: AlphaFoldClient) -> None:
        pred = await alphafold.get_prediction("P00533")
        assert pred is not None
        assert pred.alphafold_id != ""
        assert pred.sequence_length > 0

    @pytest.mark.asyncio
    async def test_health(self, alphafold: AlphaFoldClient) -> None:
        assert await alphafold.health_check()
