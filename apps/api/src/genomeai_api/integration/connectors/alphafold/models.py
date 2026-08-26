"""AlphaFold data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlphaFoldStructure:
    """AlphaFold predicted structure record."""

    alphafold_id: str
    gene_name: str = ""
    organism: str = ""
    uniprot_id: str = ""
    sequence_length: int = 0
    pae_image_url: str = ""
    cif_url: str = ""
    pae_url: str = ""
    created_date: str = ""
    confidence_version: str = ""
