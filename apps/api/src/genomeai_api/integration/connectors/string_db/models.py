"""STRING data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StringIDMapping:
    """Mapping from gene name to STRING identifier."""

    query_item: str
    string_id: str
    preferred_name: str
    annotation: str = ""
    ncbi_taxon_id: int = 9606


@dataclass(frozen=True, slots=True)
class StringInteraction:
    """A protein-protein interaction edge from STRING."""

    string_id_a: str
    string_id_b: str
    preferred_name_a: str
    preferred_name_b: str
    score: float = 0.0
    experimental_score: float = 0.0
    database_score: float = 0.0
    text_mining_score: float = 0.0
    ncbi_taxon_id: int = 9606


@dataclass(frozen=True, slots=True)
class StringEnrichment:
    """Functional enrichment result from STRING."""

    category: str
    term: str
    description: str
    number_of_genes: int = 0
    p_value: float = 0.0
    fdr: float = 0.0
    preferred_names: list[str] = field(default_factory=list)
