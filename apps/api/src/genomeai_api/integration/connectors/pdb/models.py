"""PDB data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PDBStructure:
    """PDB structure record."""

    pdb_id: str
    title: str = ""
    method: str = ""
    resolution: float = 0.0
    organism: str = ""
    gene_names: list[str] = field(default_factory=list)
    chain_count: int = 0
    deposition_date: str = ""
    keywords: list[str] = field(default_factory=list)
