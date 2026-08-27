"""KEGG data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class KEGGPathway:
    """A KEGG pathway."""

    pathway_id: str
    name: str
    organism: str = "hsa"


@dataclass(frozen=True, slots=True)
class KEGGPathwayDetail:
    """Detailed KEGG pathway information."""

    pathway_id: str
    name: str
    description: str = ""
    organism: str = ""
    genes: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class KEGGGenePathway:
    """Mapping from a gene to its KEGG pathways."""

    gene_id: str
    pathways: list[KEGGPathway]
