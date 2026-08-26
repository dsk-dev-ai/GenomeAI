"""Drug analysis API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DrugSearchRequest(BaseModel):
    query: str = Field(..., description="Drug name to search")
    max_results: int = Field(default=5, ge=1, le=20, description="Max results")


class DrugAnalyzeRequest(BaseModel):
    query: str = Field(..., description="Drug name to analyze")


class DrugSearchResponse(BaseModel):
    query: str
    chembl_drugs: list[dict[str, object]] = []
    pubchem_compound: dict[str, object] | None = None


class DrugAnalyzeResponse(BaseModel):
    query: str
    ai_analysis: str | dict[str, object] | None = None
    error: str | None = None
