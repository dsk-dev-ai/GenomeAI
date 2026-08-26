"""UniProt data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UniProtProtein:
    """UniProt protein record."""

    accession: str
    entry_name: str = ""
    protein_name: str = ""
    gene_names: list[str] = field(default_factory=list)
    organism: str = ""
    length: int = 0
    mass: float = 0.0
    function: str = ""
    keywords: list[str] = field(default_factory=list)
    subcellular_location: str = ""
    sequence: str = ""
    pdb_ids: list[str] = field(default_factory=list)
    alphafold_id: str = ""
