"""Real API tests for drug search connectors (ChEMBL + PubChem)."""

from __future__ import annotations

import pytest
from genomeai_api.integration.connectors.chembl.client import ChEMBLClient
from genomeai_api.integration.connectors.pubchem.client import PubChemClient


@pytest.mark.asyncio
class TestChEMBL:
    async def test_search_aspirin(self) -> None:
        client = ChEMBLClient()
        try:
            drugs = await client.search_drugs("aspirin", max_results=3)
            assert len(drugs) >= 1
            assert drugs[0].name != ""
            print(f"  ChEMBL aspirin: {len(drugs)} drugs")
            print(f"  First: {drugs[0].name}")
        finally:
            await client.close()

    async def test_get_drug(self) -> None:
        client = ChEMBLClient()
        try:
            drug = await client.get_drug("CHEMBL25")
            assert drug is not None
            assert drug.molecule_chembl_id == "CHEMBL25"
            print(f"  Drug: {drug.name} ({drug.molecule_chembl_id})")
        finally:
            await client.close()

    async def test_health(self) -> None:
        client = ChEMBLClient()
        try:
            assert await client.health_check()
        finally:
            await client.close()


@pytest.mark.asyncio
class TestPubChem:
    async def test_search_aspirin(self) -> None:
        client = PubChemClient()
        try:
            compound = await client.search_by_name("aspirin")
            assert compound is not None
            assert compound.cid > 0
            assert compound.molecular_formula != ""
            print(f"  PubChem aspirin: CID {compound.cid}")
            print(f"  Formula: {compound.molecular_formula}")
            print(f"  MW: {compound.molecular_weight}")
        finally:
            await client.close()

    async def test_health(self) -> None:
        client = PubChemClient()
        try:
            assert await client.health_check()
        finally:
            await client.close()
