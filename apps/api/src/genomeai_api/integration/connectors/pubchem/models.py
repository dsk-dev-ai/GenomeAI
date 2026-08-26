"""PubChem data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PubChemCompound:
    """PubChem compound record."""

    cid: int = 0
    name: str = ""
    molecular_formula: str = ""
    molecular_weight: float = 0.0
    iupac_name: str = ""
    canonical_smiles: str = ""
    inchi: str = ""
    xlogp: float = 0.0
    hydrogen_bond_donor_count: int = 0
    hydrogen_bond_acceptor_count: int = 0
    description: str = ""
    drug_interactions: list[str] = field(default_factory=list)
