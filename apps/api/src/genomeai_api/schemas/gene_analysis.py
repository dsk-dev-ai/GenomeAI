"""Gene analysis schemas — Pydantic models for gene analysis API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneAnalyzeRequest(BaseModel):
    """Request to analyze a gene."""

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Gene symbol (e.g., BRCA1, TP53)",
        examples=["BRCA1"],
    )
    organism: str = Field(
        default="Homo sapiens",
        description="Organism name",
    )


class GeneAnalyzeResponse(BaseModel):
    """Response from gene analysis."""

    gene_symbol: str
    gene_id: str
    name: str
    organism: str = ""
    chromosome: str = ""
    map_location: str = ""
    description: str = ""
    aliases: list[str] = []
    gene_type: str = ""
    function: str = ""
    key_variants: list[str] = []
    associated_diseases: list[str] = []
    drug_targets: list[str] = []
    clinical_significance: str = ""
    summary: str = ""
    source: str = ""


class GeneSearchRequest(BaseModel):
    """Request to search genes."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Search query (gene name, symbol, or description)",
    )
    organism: str = Field(default="Homo sapiens")
    max_results: int = Field(default=20, ge=1, le=100)


class GeneSearchResult(BaseModel):
    """Single gene search result."""

    gene_id: str
    symbol: str
    name: str
    organism: str = ""
    chromosome: str = ""
    map_location: str = ""
    description: str = ""
    gene_type: str = ""


class GeneSearchResponse(BaseModel):
    """Response from gene search."""

    query: str
    count: int
    results: list[GeneSearchResult]
