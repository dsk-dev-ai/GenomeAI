"""Europe PMC data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EuropePMCArticle:
    """Europe PMC article record."""

    pmid: str = ""
    pmcid: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    pub_date: str = ""
    abstract: str = ""
    doi: str = ""
    cited_by_count: int = 0
    keywords: list[str] = field(default_factory=list)
    open_access: bool = False
