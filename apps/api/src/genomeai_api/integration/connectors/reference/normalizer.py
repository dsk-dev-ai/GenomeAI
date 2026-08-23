"""Normalizer for ``genomeai-reference`` records.

Deterministically converts one raw external record into the canonical
intermediate shape (`NormalizedEntity`) that future Phase 7 ingestions would
map onto real GenomeAI entities. Determinism matters: the same input always
produces byte-identical output.
"""

from __future__ import annotations

from typing import cast

from genomeai_api.integration.connectors.reference.connector import ReferenceRecord
from genomeai_api.integration.errors import NormalizationError
from genomeai_api.integration.normalizers.base import NormalizedEntity
from genomeai_api.integration.raw_data import RawRecord
from genomeai_api.integration.types import EntityType


class ReferenceRecordNormalizer:
    """Raw reference record → canonical gene-shaped entity (illustrative)."""

    entity_type = EntityType.GENE

    def normalize_payload(self, record: ReferenceRecord) -> NormalizedEntity:
        if not record.record_id or not record.symbol:
            raise NormalizationError(
                "Reference record requires both 'record_id' and 'symbol'",
            )
        return NormalizedEntity(
            entity_type=self.entity_type.value,
            entity_id=f"{record.record_id}",
            fields={
                "source_symbol": record.symbol,
                "name": record.name,
                "external_id": record.record_id,
                "source_version": record.source_version,
            },
        )

    def normalize(self, record: RawRecord) -> NormalizedEntity:
        """Adapts a `RawRecord` whose payload is a reference-record dict."""
        payload = record.payload
        if not isinstance(payload, dict):
            raise NormalizationError(
                "Cannot normalize a non-object reference payload",
            )
        data = cast(dict[str, object], payload)
        try:
            parsed = ReferenceRecord(
                record_id=str(data["record_id"]),
                symbol=str(data["symbol"]),
                name=str(data["name"]),
            )
        except KeyError as exc:
            raise NormalizationError(
                f"Reference payload is missing field '{exc.args[0]}'",
            ) from exc
        return self.normalize_payload(parsed)
