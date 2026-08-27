"""Disease analysis API router."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.schemas.disease_analysis import (
    DiseaseAnalysisRequest,
    DiseaseAnalysisResponse,
    DiseaseInfo,
    GeneDiseaseAssociation,
    MonarchDiseaseResult,
)
from genomeai_api.services.disease_analysis import DiseaseAnalysisEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diseases", tags=["diseases"])


def _get_engine() -> DiseaseAnalysisEngine:
    return DiseaseAnalysisEngine(ai_provider=GeminiProvider())


def _parse_ai_json(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


@router.post("/search", response_model=DiseaseAnalysisResponse)
async def search_disease(request: DiseaseAnalysisRequest) -> DiseaseAnalysisResponse:
    """Search for diseases by name and get AI analysis."""
    engine = _get_engine()
    try:
        result = await engine.search_disease(request.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await engine.close()

    diseases = [
        DiseaseInfo(
            disease_id=str(d.disease_id),
            name=str(d.name),
            description=str(d.description),
        )
        for d in result.diseases
    ]
    associations = [
        GeneDiseaseAssociation(
            gene_symbol=str(a.gene_symbol),
            gene_id=str(a.gene_id),
            disease_name=str(a.disease_name),
            disease_id=str(a.disease_id),
            score=float(a.score),
        )
        for a in result.gene_disease_associations
    ]
    monarch = [
        MonarchDiseaseResult(
            disease_id=str(m.disease_id),
            disease_name=str(m.disease_name),
            category=str(m.category),
        )
        for m in result.monarch_results
    ]

    return DiseaseAnalysisResponse(
        query=result.query,
        diseases=diseases,
        gene_disease_associations=associations,
        monarch_results=monarch,
        ai_analysis=_parse_ai_json(result.ai_raw_response),
        sources=result.sources,
    )


@router.post("/gene", response_model=DiseaseAnalysisResponse)
async def analyze_gene_diseases(request: DiseaseAnalysisRequest) -> DiseaseAnalysisResponse:
    """Find diseases associated with a gene."""
    engine = _get_engine()
    try:
        result = await engine.analyze_gene_diseases(request.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await engine.close()

    diseases = [
        DiseaseInfo(
            disease_id=str(d.disease_id),
            name=str(d.name),
            description=str(d.description),
        )
        for d in result.diseases
    ]
    associations = [
        GeneDiseaseAssociation(
            gene_symbol=str(a.gene_symbol),
            gene_id=str(a.gene_id),
            disease_name=str(a.disease_name),
            disease_id=str(a.disease_id),
            score=float(a.score),
        )
        for a in result.gene_disease_associations
    ]
    monarch = [
        MonarchDiseaseResult(
            disease_id=str(m.disease_id),
            disease_name=str(m.disease_name),
            category=str(m.category),
        )
        for m in result.monarch_results
    ]

    return DiseaseAnalysisResponse(
        query=result.query,
        diseases=diseases,
        gene_disease_associations=associations,
        monarch_results=monarch,
        ai_analysis=_parse_ai_json(result.ai_raw_response),
        sources=result.sources,
    )
