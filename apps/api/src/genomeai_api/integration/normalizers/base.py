"""Normalization boundary.

A source-specific record becomes plain, validated, deterministic data that a
future ingestion pipeline can persist as a GenomeAI canonical entity. The
boundary makes no claim about the biological meaning of the values — it only
moves an external record into an intermediate, source-neutral shape.

The minimal example here (entity kind + identifier + keys + extras) is the
contract every source normalizer converges on. Full NCBI/Ensembl normalizers
are later milestones that implement the same interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from genomeai_api.integration.raw_data import RawRecord


@dataclass(frozen=True)
class NormalizedEntity:
    """Canonical (source-neutral) shape a normalized record must expose."""

    entity_type: str
    entity_id: str
    # 1..N source-specific fields kept for depth (never secrets).
    fields: dict[str, object] = field(default_factory=dict)
    provenance: object | None = None


class Normalizer(Protocol):
    """Converts one raw external record into a canonical entity."""

    def normalize(self, record: RawRecord) -> NormalizedEntity: ...


@dataclass(frozen=True)
class ValidationIssue:
    """A single problem found while validating external data."""

    code: str
    message: str
