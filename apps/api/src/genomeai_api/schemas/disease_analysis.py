"""Disease analysis schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DiseaseInfo(BaseModel):
    """A disease entity."""

    disease_id: str = ""
    name: str = ""
    description: str = ""


class GeneDiseaseAssociation(BaseModel):
    """Gene-disease association from OpenTargets."""

    gene_symbol: str = ""
    gene_id: str = ""
    disease_name: str = ""
    disease_id: str = ""
    score: float = 0.0


class MonarchDiseaseResult(BaseModel):
    """Monarch disease association."""

    disease_id: str = ""
    disease_name: str = ""
    category: str = ""


class DiseaseAnalysisRequest(BaseModel):
    """Request for disease analysis."""

    query: str
    genes: list[str] = []


class DiseaseAnalysis(BaseModel):
    """Internal disease analysis result."""

    query: str
    diseases: list[DiseaseInfo] = []
    gene_disease_associations: list[GeneDiseaseAssociation] = []
    monarch_results: list[MonarchDiseaseResult] = []
    ai_raw_response: str = ""
    sources: list[str] = []


class DiseaseAnalysisResponse(BaseModel):
    """Response from disease analysis."""

    query: str
    diseases: list[DiseaseInfo] = []
    gene_disease_associations: list[GeneDiseaseAssociation] = []
    monarch_results: list[MonarchDiseaseResult] = []
    ai_analysis: str = ""
    sources: list[str] = []
