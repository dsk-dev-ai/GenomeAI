"""ChEMBL data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChEMBLDrug:
    """ChEMBL molecule record."""

    molecule_chembl_id: str = ""
    name: str = ""
    molecule_type: str = ""
    max_phase: int = 0
    therapeutic_area: list[str] = field(default_factory=list)
    mechanism_of_action: str = ""
    target_chembl_id: str = ""
    target_name: str = ""
    target_organism: str = ""
    smiles: str = ""
    pref_name: str = ""


@dataclass(frozen=True)
class ChEMBLBioactivity:
    """ChEMBL bioactivity record."""

    activity_id: str = ""
    target_name: str = ""
    assay_type: str = ""
    standard_type: str = ""
    standard_value: float = 0.0
    standard_units: str = ""
    standard_relation: str = ""
    pchembl_value: float = 0.0
