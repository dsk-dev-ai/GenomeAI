"""Drug analysis API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.schemas.drug_analysis import (
    DrugAnalyzeRequest,
    DrugAnalyzeResponse,
    DrugSearchRequest,
    DrugSearchResponse,
)
from genomeai_api.services.drug_analysis import DrugAnalysisEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/drugs", tags=["drugs"])


def _get_engine() -> DrugAnalysisEngine:
    return DrugAnalysisEngine(ai_provider=GeminiProvider())


@router.post("/search", response_model=DrugSearchResponse)
async def search_drugs(request: DrugSearchRequest) -> DrugSearchResponse:
    engine = _get_engine()
    try:
        results = await engine.search(request.query)
        raw_chembl = results.get("chembl_drugs", [])
        chembl_drugs: list[dict[str, object]] = (
            raw_chembl if isinstance(raw_chembl, list) else []
        )
        raw_pc = results.get("pubchem_compound")
        pc_compound: dict[str, object] | None = (
            raw_pc if isinstance(raw_pc, dict) else None
        )
        return DrugSearchResponse(
            query=str(results.get("query", request.query)),
            chembl_drugs=chembl_drugs,
            pubchem_compound=pc_compound,
        )
    except Exception as exc:
        logger.error("Drug search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await engine.close()


@router.post("/analyze", response_model=DrugAnalyzeResponse)
async def analyze_drug(request: DrugAnalyzeRequest) -> DrugAnalyzeResponse:
    engine = _get_engine()
    try:
        results = await engine.analyze(request.query)
        raw_analysis = results.get("ai_analysis")
        if isinstance(raw_analysis, str):
            ai_analysis: str | dict[str, object] | None = raw_analysis
        elif isinstance(raw_analysis, dict):
            ai_analysis = raw_analysis
        else:
            ai_analysis = None
        raw_error = results.get("error")
        error_val: str | None = (
            str(raw_error) if isinstance(raw_error, str) else None
        )
        return DrugAnalyzeResponse(
            query=str(results.get("query", request.query)),
            ai_analysis=ai_analysis,
            error=error_val,
        )
    except Exception as exc:
        logger.error("Drug analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await engine.close()
