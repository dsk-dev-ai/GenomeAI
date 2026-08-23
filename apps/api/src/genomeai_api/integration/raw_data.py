"""Raw external record boundary (reproducibility).

Before any external payload is normalized, GenomeAI keeps a lean, extensible
record of what was retrieved, from where, when, and its digest. This is the
foundation for provenance and reproducibility without designing a large
raw-storage engine now.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime


def checksum_bytes(raw: bytes) -> str:
    """Stable SHA-256 hex digest of a raw payload (for integrity checks)."""
    return hashlib.sha256(raw).hexdigest()


def checksum_json(payload: object) -> str:
    """Checksum of a JSON-serializable payload with deterministic ordering."""
    return checksum_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def utc_now_iso() -> str:
    """Current UTC timestamp as ISO-8601 string (shared default)."""
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class RawRecord:
    """Minimal raw external record saved before normalization.

    ``payload`` may be an unwieldy object; a future storage layer can persist
    it to object storage and keep a ``payload_ref`` here. The interface stays
    small so the boundary does not commit to an enormous raw store prematurely.
    """

    source: str
    source_id: str
    source_version: str | None = None
    retrieved_at: str | None = None
    payload: object | None = None
    payload_ref: str | None = None
    payload_sha256: str | None = None

    def with_checksum(self) -> RawRecord:
        """Returns a copy with ``payload_sha256`` derived from the payload."""
        if isinstance(self.payload, bytes):
            digest = checksum_bytes(self.payload)
        elif self.payload is not None:
            digest = checksum_json(self.payload)
        else:
            digest = None
        return RawRecord(
            source=self.source,
            source_id=self.source_id,
            source_version=self.source_version,
            retrieved_at=self.retrieved_at,
            payload=self.payload,
            payload_ref=self.payload_ref,
            payload_sha256=digest,
        )


@dataclass(frozen=True)
class ProvenanceRecord:
    """Traceability of an imported external record (Phase 7 foundation).

    No source release is fabricated here: ``source_release`` is ``None`` until
    a connector reports a real release/version. ``retrieved_at`` is filled by
    the fetcher layer at fetch time, not invented downstream.
    """

    source: str
    source_record_id: str
    source_release: str | None = None
    retrieved_at: str = field(default_factory=utc_now_iso)
    ingested_at: str = field(default_factory=utc_now_iso)
    checksum: str | None = None
    source_url: str | None = None
