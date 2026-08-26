"""Ensembl VEP data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class VEPConsequence:
    """Single transcript consequence from VEP."""

    transcript_id: str = ""
    gene_symbol: str = ""
    gene_id: str = ""
    biotype: str = ""
    consequence_terms: list[str] = field(default_factory=list)
    impact: str = ""
    sift_score: float | None = None
    sift_prediction: str = ""
    polyphen_score: float | None = None
    polyphen_prediction: str = ""
    codons: str = ""
    amino_acids: str = ""
    cdna_start: int | None = None
    cdna_end: int | None = None
    cds_start: int | None = None
    cds_end: int | None = None
    protein_start: int | None = None
    protein_end: int | None = None
    exon: str = ""
    intron: str = ""


@dataclass(frozen=True)
class VEPResult:
    """Full VEP prediction result."""

    input: str = ""
    start: int | None = None
    end: int | None = None
    allele: str = ""
    strand: int = 0
    rs_id: str = ""
    consequences: list[VEPConsequence] = field(default_factory=list)
