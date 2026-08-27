"""Reactome data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReactomePathway:
    """A Reactome pathway."""

    db_id: int
    st_id: str
    name: str
    species: str = "Homo sapiens"
    schema_class: str = "Pathway"
    compartment_names: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ReactomeParticipant:
    """A participant entity in a Reactome pathway."""

    db_id: int
    display_name: str
    schema_class: str
    ref_identifiers: list[str] = field(default_factory=list)
    ref_names: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ReactomeSearchResult:
    """Search results from Reactome."""

    total_matches: int
    pathways: list[ReactomePathway]
