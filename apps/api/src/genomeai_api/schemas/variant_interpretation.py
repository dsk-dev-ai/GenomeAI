"""Variant interpretation schemas — Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VariantInterpretRequest(BaseModel):
    """Request to interpret a variant."""

    gene: str = Field(..., min_length=1, max_length=50, description="Gene symbol")
    hgvs_c: str = Field(default="", description="HGVS cDNA notation (optional)")
    clinvar_id: str = Field(default="", description="ClinVar ID (optional)")
    max_variants: int = Field(default=5, ge=1, le=20)


class ClinVarInfo(BaseModel):
    clinvar_id: str = ""
    clinical_significance: str = ""
    review_status: str = ""
    condition: str = ""
    hgvs_c: str = ""
    hgvs_p: str = ""


class GnomADInfo(BaseModel):
    variant_id: str = ""
    allele_frequency: float = 0.0
    allele_count: int = 0
    allele_number: int = 0


class VEPInfo(BaseModel):
    consequence: str = ""
    impact: str = ""
    sift_prediction: str = ""
    sift_score: float | None = None
    polyphen_prediction: str = ""
    polyphen_score: float | None = None


class VariantInterpretResponse(BaseModel):
    """Response from variant interpretation."""

    variant_description: str = ""
    gene_symbol: str = ""
    clinvar: ClinVarInfo | None = None
    gnomad: GnomADInfo | None = None
    vep: VEPInfo | None = None
    pathogenicity: str = ""
    acmg_criteria: list[str] = []
    reasoning: str = ""
    clinical_actionability: str = ""
    summary: str = ""
    data_sources: list[str] = []


class VariantSearchRequest(BaseModel):
    """Request to search variants by gene."""

    gene: str = Field(..., min_length=1, max_length=50)
    significance: str = Field(default="", description="Pathogenic, Benign, etc.")
    max_results: int = Field(default=20, ge=1, le=100)


class VariantSearchResult(BaseModel):
    clinvar_id: str = ""
    gene_symbol: str = ""
    clinical_significance: str = ""
    condition: str = ""
    hgvs_c: str = ""
    hgvs_p: str = ""


class VariantSearchResponse(BaseModel):
    gene: str
    count: int
    results: list[VariantSearchResult]
