"""Literature search API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from genomeai_api.ai.gemini import GeminiProvider
from genomeai_api.schemas.literature_search import (
    LiteratureAnalyzeRequest,
    LiteratureAnalyzeResponse,
    LiteratureSearchRequest,
    LiteratureSearchResponse,
)
from genomeai_api.services.literature_search import LiteratureSearchEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/literature", tags=["literature"])


def _get_engine() -> LiteratureSearchEngine:
    return LiteratureSearchEngine(ai_provider=GeminiProvider())


@router.post("/search", response_model=LiteratureSearchResponse)
async def search_literature(request: LiteratureSearchRequest) -> LiteratureSearchResponse:
    engine = _get_engine()
    try:
        results = await engine.search(request.query, max_results=request.max_results)
        raw_query = results.get("query", "")
        query = str(raw_query) if isinstance(raw_query, str) else request.query
        raw_epmc = results.get("europepmc_count", 0)
        epmc_count = int(raw_epmc) if isinstance(raw_epmc, (int, float)) else 0
        raw_ss = results.get("semanticscholar_count", 0)
        ss_count = int(raw_ss) if isinstance(raw_ss, (int, float)) else 0
        raw_epmc_articles = results.get("europepmc_articles", [])
        epmc_articles: list[dict[str, object]] = (
            raw_epmc_articles if isinstance(raw_epmc_articles, list) else []
        )
        raw_ss_papers = results.get("semanticscholar_papers", [])
        ss_papers: list[dict[str, object]] = (
            raw_ss_papers if isinstance(raw_ss_papers, list) else []
        )
        return LiteratureSearchResponse(
            query=query,
            europepmc_count=epmc_count,
            semanticscholar_count=ss_count,
            europepmc_articles=epmc_articles,
            semanticscholar_papers=ss_papers,
        )
    except Exception as exc:
        logger.error("Literature search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await engine.close()


@router.post("/analyze", response_model=LiteratureAnalyzeResponse)
async def analyze_literature(request: LiteratureAnalyzeRequest) -> LiteratureAnalyzeResponse:
    engine = _get_engine()
    try:
        results = await engine.analyze(request.query, max_results=request.max_results)
        raw_query = results.get("query", request.query)
        query = str(raw_query) if isinstance(raw_query, str) else request.query
        raw_count = results.get("papers_count", 0)
        papers_count = int(raw_count) if isinstance(raw_count, (int, float)) else 0
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
        return LiteratureAnalyzeResponse(
            query=query,
            papers_count=papers_count,
            ai_analysis=ai_analysis,
            error=error_val,
        )
    except Exception as exc:
        logger.error("Literature analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await engine.close()
