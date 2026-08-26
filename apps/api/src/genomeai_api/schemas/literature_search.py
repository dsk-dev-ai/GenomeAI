"""Literature API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LiteratureSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for biomedical literature")
    max_results: int = Field(default=10, ge=1, le=50, description="Max results per source")


class LiteratureAnalyzeRequest(BaseModel):
    query: str = Field(..., description="Search query for literature analysis")
    max_results: int = Field(default=5, ge=1, le=20, description="Max papers to analyze")


class LiteratureSearchResponse(BaseModel):
    query: str
    europepmc_count: int = 0
    semanticscholar_count: int = 0
    europepmc_articles: list[dict[str, object]] = []
    semanticscholar_papers: list[dict[str, object]] = []


class LiteratureAnalyzeResponse(BaseModel):
    query: str
    papers_count: int = 0
    ai_analysis: str | dict[str, object] | None = None
    error: str | None = None
