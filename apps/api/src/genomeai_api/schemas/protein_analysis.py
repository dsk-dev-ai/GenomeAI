"""Protein analysis schemas — Pydantic models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProteinAnalyzeRequest(BaseModel):
    """Request to analyze a protein."""

    gene: str = Field(default="", description="Gene symbol")
    accession: str = Field(default="", description="UniProt accession")


class PDBInfo(BaseModel):
    pdb_id: str = ""
    title: str = ""
    method: str = ""
    resolution: float = 0.0


class AlphaFoldInfo(BaseModel):
    alphafold_id: str = ""
    sequence_length: int = 0
    confidence_version: str = ""


class ProteinAnalyzeResponse(BaseModel):
    """Response from protein analysis."""

    protein_name: str = ""
    accession: str = ""
    gene_names: list[str] = []
    organism: str = ""
    length: int = 0
    function: str = ""
    subcellular_location: str = ""
    pdb_structures: list[PDBInfo] = []
    alphafold: AlphaFoldInfo | None = None
    function_summary: str = ""
    domains: list[str] = []
    clinical_significance: str = ""
    drug_targets: list[str] = []
    disease_associations: list[str] = []
    structural_notes: str = ""
    summary: str = ""
    data_sources: list[str] = []


class ProteinSearchRequest(BaseModel):
    """Request to search proteins by gene."""

    query: str = Field(..., min_length=1, max_length=100)
    max_results: int = Field(default=5, ge=1, le=20)


class ProteinSearchResult(BaseModel):
    accession: str = ""
    entry_name: str = ""
    protein_name: str = ""
    gene_names: list[str] = []
    organism: str = ""
    length: int = 0


class ProteinSearchResponse(BaseModel):
    query: str
    count: int
    results: list[ProteinSearchResult]
