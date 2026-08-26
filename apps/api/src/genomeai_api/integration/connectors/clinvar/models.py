"""ClinVar data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClinVarRecord:
    """ClinVar variant interpretation record."""

    clinvar_id: str
    gene_symbol: str
    clinical_significance: str
    review_status: str = ""
    condition: str = ""
    variant_type: str = ""
    chromosome: str = ""
    start: int | None = None
    end: int | None = None
    ref_allele: str = ""
    alt_allele: str = ""
    hgvs_c: str = ""
    hgvs_p: str = ""
    summary: str = ""
