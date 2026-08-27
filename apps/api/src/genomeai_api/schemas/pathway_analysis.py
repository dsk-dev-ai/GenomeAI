"""Pathway analysis API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PathwayAnalysisRequest(BaseModel):
    """Request for pathway analysis."""

    gene: str = Field(..., description="Gene symbol (e.g. 'BRCA1')")
    genes: list[str] = Field(
        default_factory=list,
        description="Additional genes for multi-gene pathway analysis",
    )


class PathwayInfo(BaseModel):
    """A single pathway entry."""

    name: str = ""
    st_id: str = ""
    pathway_id: str = ""
    description: str = ""
    species: str = ""
    p_value: float | None = None
    fdr: float | None = None


class InteractionInfo(BaseModel):
    """A protein interaction entry."""

    partner: str = ""
    from_gene: str = ""
    to_gene: str = ""
    score: float = 0.0


class EnrichmentInfo(BaseModel):
    """Functional enrichment entry."""

    category: str = ""
    term: str = ""
    description: str = ""
    p_value: float = 0.0
    fdr: float = 0.0


class PathwayAnalysisResponse(BaseModel):
    """Complete pathway analysis response."""

    query: str
    reactome_pathways: list[PathwayInfo] = Field(default_factory=list)
    kegg_pathways: list[PathwayInfo] = Field(default_factory=list)
    string_interactions: list[InteractionInfo] = Field(default_factory=list)
    string_enrichment: list[EnrichmentInfo] = Field(default_factory=list)
    ai_analysis: str = ""
    sources: list[str] = Field(default_factory=list)
