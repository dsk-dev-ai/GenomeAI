"""gnomAD data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GnomADVariant:
    """gnomAD variant frequency record."""

    variant_id: str
    chromosome: str = ""
    start: int | None = None
    ref: str = ""
    alt: str = ""
    exome_ac: int = 0
    exome_an: int = 0
    exome_af: float = 0.0
    genome_ac: int = 0
    genome_an: int = 0
    genome_af: float = 0.0
    ClinVar_id: str = ""
    clinical_significance: str = ""
