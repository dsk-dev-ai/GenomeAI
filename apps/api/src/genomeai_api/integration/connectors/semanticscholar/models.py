"""Semantic Scholar data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticScholarPaper:
    """Semantic Scholar paper record."""

    paper_id: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    year: int = 0
    citation_count: int = 0
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    open_access: bool = False
    fields_of_study: list[str] = field(default_factory=list)
    url: str = ""
