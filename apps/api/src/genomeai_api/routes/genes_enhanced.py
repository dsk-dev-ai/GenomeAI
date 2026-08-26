"""Gene analysis API endpoints — search and analyze genes with real data.

Uses NCBI E-utilities for real gene data + Gemini for AI analysis.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.schemas.gene_analysis import (
    GeneAnalyzeRequest,
    GeneAnalyzeResponse,
    GeneSearchRequest,
    GeneSearchResponse,
    GeneSearchResult,
)
from genomeai_api.services.gene_analysis import GeneAnalysisEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/genes", tags=["gene-analysis"])


def _get_engine() -> GeneAnalysisEngine:
    """Create gene analysis engine with default providers."""
    return GeneAnalysisEngine(
        ai_provider=GeminiProvider(),
        ncbi_client=NCBIClient(),
    )


@router.post("/analyze", response_model=GeneAnalyzeResponse)
async def analyze_gene(request: GeneAnalyzeRequest) -> GeneAnalyzeResponse:
    """Analyze a gene by symbol using real NCBI data + AI.

    Fetches real gene data from NCBI E-utilities, then uses Ollama
    to generate a structured analysis including function, variants,
    diseases, drug targets, and clinical significance.
    """
    engine = _get_engine()
    try:
        analysis = await engine.analyze_by_symbol(
            symbol=request.symbol,
            organism=request.organism,
        )
        return GeneAnalyzeResponse(
            gene_symbol=analysis.gene_symbol,
            gene_id=analysis.gene_id,
            name=analysis.name,
            organism=analysis.organism,
            chromosome=analysis.chromosome,
            map_location=analysis.map_location,
            description=analysis.description,
            aliases=analysis.aliases,
            gene_type=analysis.gene_type,
            function=analysis.function,
            key_variants=analysis.key_variants,
            associated_diseases=analysis.associated_diseases,
            drug_targets=analysis.drug_targets,
            clinical_significance=analysis.clinical_significance,
            summary=analysis.summary,
            source=analysis.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Gene analysis failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Gene analysis failed: {exc}",
        )
    finally:
        await engine.close()


@router.post("/search", response_model=GeneSearchResponse)
async def search_genes(request: GeneSearchRequest) -> GeneSearchResponse:
    """Search for genes by name or symbol using real NCBI data."""
    client = NCBIClient()
    try:
        records = await client.search_genes(
            query=request.query,
            organism=request.organism,
            max_results=request.max_results,
        )
        return GeneSearchResponse(
            query=request.query,
            count=len(records),
            results=[
                GeneSearchResult(
                    gene_id=r.gene_id,
                    symbol=r.symbol,
                    name=r.name,
                    organism=r.organism,
                    chromosome=r.chromosome,
                    map_location=r.map_location,
                    description=r.description,
                    gene_type=r.gene_type,
                )
                for r in records
            ],
        )
    except Exception as exc:
        logger.error("Gene search failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Gene search failed: {exc}",
        )
    finally:
        await client.close()
