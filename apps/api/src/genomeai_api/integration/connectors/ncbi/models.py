"""Data models for NCBI E-utilities responses."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NCBISearchResult:
    """Result from NCBI esearch."""

    database: str
    count: int
    ids: list[str]
    query_translation: str = ""


@dataclass(frozen=True)
class NCBIGeneRecord:
    """Normalized gene record from NCBI efetch."""

    gene_id: str
    symbol: str
    name: str
    organism: str = "Homo sapiens"
    chromosome: str = ""
    location: str = ""
    map_location: str = ""
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    gene_type: str = ""
    summary: str = ""
    genomic_accession: str = ""
    genomic_start: int | None = None
    genomic_end: int | None = None
    strand: str = ""


@dataclass(frozen=True)
class NCBISequenceRecord:
    """Sequence record from NCBI efetch."""

    accession: str
    sequence: str
    definition: str = ""
    organism: str = ""
    length: int = 0


@dataclass(frozen=True)
class NCBIRefLinkRecord:
    """Cross-reference record from NCBI elink."""

    source_db: str
    source_id: str
    target_db: str
    target_id: str
    target_label: str = ""
