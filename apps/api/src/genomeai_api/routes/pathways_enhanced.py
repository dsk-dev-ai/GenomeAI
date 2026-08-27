"""Pathway analysis API router."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.schemas.pathway_analysis import (
    EnrichmentInfo,
    InteractionInfo,
    PathwayAnalysisRequest,
    PathwayAnalysisResponse,
    PathwayInfo,
)
from genomeai_api.services.pathway_analysis import PathwayAnalysisEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pathways", tags=["pathways"])


def _get_engine() -> PathwayAnalysisEngine:
    return PathwayAnalysisEngine(ai_provider=GeminiProvider())


def _parse_ai_json(raw: str) -> str:
    """Try to extract meaningful text from AI response."""
    if not raw:
        return ""
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


@router.post("/analyze", response_model=PathwayAnalysisResponse)
async def analyze_pathway(request: PathwayAnalysisRequest) -> PathwayAnalysisResponse:
    """Analyze pathways for a gene using Reactome, STRING, KEGG + AI."""
    engine = _get_engine()
    try:
        if request.genes:
            result = await engine.analyze_by_gene_list(
                [request.gene, *request.genes],
            )
        else:
            result = await engine.analyze_by_gene(request.gene)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        await engine.close()

    reactome = [
        PathwayInfo(
            name=str(p.get("name", "")),
            st_id=str(p.get("st_id", "")),
            species=str(p.get("species", "")),
        )
        for p in result.reactome_pathways
    ]
    kegg = [
        PathwayInfo(
            name=str(p.get("name", "")),
            pathway_id=str(p.get("pathway_id", "")),
        )
        for p in result.kegg_pathways
    ]
    interactions = [
        InteractionInfo(
            partner=str(i.get("partner", i.get("to", ""))),
            from_gene=str(i.get("from", "")),
            to_gene=str(i.get("to", i.get("partner", ""))),
            score=float(str(i.get("score", 0))),
        )
        for i in result.string_interactions
    ]
    enrichment = [
        EnrichmentInfo(
            category=str(e.get("category", "")),
            term=str(e.get("term", "")),
            description=str(e.get("description", "")),
            p_value=float(str(e.get("p_value", 0))),
            fdr=float(str(e.get("fdr", 0))),
        )
        for e in result.string_enrichment
    ]

    return PathwayAnalysisResponse(
        query=result.query,
        reactome_pathways=reactome,
        kegg_pathways=kegg,
        string_interactions=interactions,
        string_enrichment=enrichment,
        ai_analysis=_parse_ai_json(result.ai_raw_response),
        sources=result.sources,
    )
