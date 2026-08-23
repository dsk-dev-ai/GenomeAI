"""External identifiers: cross-database identifier federation.

A single ``ExternalIdentifier`` concept maps external record ids (NCBI Gene ID,
Ensembl Gene ID, HGNC ID, GENCODE ID, ...) to a GenomeAI internal entity. This
avoids scattering duplicate identifier columns across biological-domain tables:
the mapping lives in one normalized table keyed by (source, external_id,
entity_type, namespace).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExternalIdentifier:
    """A stable external id → GenomeAI entity mapping (with provenance)."""

    source: str
    external_id: str
    entity_type: str
    genomeai_entity_id: uuid.UUID
    namespace: str | None = None
    version: str | None = None
    provenance: object | None = None


class ExternalIdentifierStore(Protocol):
    """Persistence seam for external identifiers.

    Implemented by the repository layer; kept Protocol-shaped so tests can
    inject a simple fake. Uniqueness of (source, external_id, entity_type,
    namespace) is enforced by the database implementation.
    """

    def create(self, identifier: ExternalIdentifier) -> ExternalIdentifier: ...

    def get(
        self,
        *,
        source: str,
        external_id: str,
        entity_type: str,
        namespace: str | None = None,
    ) -> ExternalIdentifier | None: ...

    def list_for_entity(
        self, *, entity_type: str, genomeai_entity_id: uuid.UUID
    ) -> list[ExternalIdentifier]: ...

    def list_by_source(self, *, source: str) -> list[ExternalIdentifier]: ...
