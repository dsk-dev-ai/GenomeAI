"""Tests for drug analysis service behavior."""

from __future__ import annotations

import pytest
from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse
from genomeai_api.integration.connectors.chembl.models import ChEMBLDrug
from genomeai_api.integration.connectors.pubchem.models import PubChemCompound
from genomeai_api.services.drug_analysis import DrugAnalysisEngine


class FakeAI(AIProvider):
    name = "fake"

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False

    async def generate(self, request: AIRequest) -> AIResponse:
        if self.fail:
            raise RuntimeError("no ai")
        return AIResponse(text="analysis", provider="fake")

    async def health_check(self) -> bool:
        return True

    async def list_models(self) -> list[str]:
        return ["fake"]

    async def close(self) -> None:
        self.closed = True


class FakeChEMBL:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False

    async def search_drugs(self, query: str, max_results: int = 3) -> list[ChEMBLDrug]:
        if self.fail:
            raise RuntimeError("chembl down")
        return [ChEMBLDrug(molecule_chembl_id="CHEMBL25", name="Aspirin", max_phase=4)]

    async def close(self) -> None:
        self.closed = True


class FakePubChem:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.closed = False

    async def search_by_name(self, query: str) -> PubChemCompound | None:
        if self.fail:
            raise RuntimeError("pubchem down")
        return PubChemCompound(cid=2244, name="aspirin", molecular_formula="C9H8O4")

    async def close(self) -> None:
        self.closed = True


def make_engine(ai: FakeAI | None = None) -> DrugAnalysisEngine:
    engine = DrugAnalysisEngine(ai_provider=ai or FakeAI())
    engine._chembl = FakeChEMBL()  # type: ignore[assignment]
    engine._pubchem = FakePubChem()  # type: ignore[assignment]
    return engine


@pytest.mark.asyncio
async def test_search_keeps_pubchem_when_chembl_fails() -> None:
    engine = make_engine()
    engine._chembl = FakeChEMBL(fail=True)  # type: ignore[assignment]

    result = await engine.search("aspirin")

    assert result["chembl_drugs"] == []
    assert isinstance(result["pubchem_compound"], dict)
    assert result["sources"] == ["PubChem"]


@pytest.mark.asyncio
async def test_analyze_preserves_search_data_when_ai_fails() -> None:
    engine = make_engine(FakeAI(fail=True))

    result = await engine.analyze("aspirin")

    assert result["ai_analysis"] is None
    assert result["error"] == "no ai"
    assert len(result["chembl_drugs"] if isinstance(result["chembl_drugs"], list) else []) == 1
    assert isinstance(result["pubchem_compound"], dict)


@pytest.mark.asyncio
async def test_close_closes_ai_when_engine_owns_provider() -> None:
    ai = FakeAI()
    engine = make_engine(ai)

    await engine.close()

    assert ai.closed is True
