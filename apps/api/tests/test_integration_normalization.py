from __future__ import annotations

import pytest
from genomeai_api.integration.connectors.reference.connector import ReferenceRecord
from genomeai_api.integration.connectors.reference.normalizer import (
    ReferenceRecordNormalizer,
)
from genomeai_api.integration.errors import NormalizationError
from genomeai_api.integration.raw_data import RawRecord
from genomeai_api.integration.types import EntityType

NORMALIZER = ReferenceRecordNormalizer()


def _record() -> ReferenceRecord:
    return ReferenceRecord(
        record_id="REF:1001", symbol="TP53", name="Tumor protein p53", source_version="1"
    )


def test_normalizes_reference_record_to_canonical_gene() -> None:
    entity = NORMALIZER.normalize_payload(_record())
    assert entity.entity_type == EntityType.GENE.value
    assert entity.entity_id == "REF:1001"
    assert entity.fields["source_symbol"] == "TP53"


def test_normalization_is_deterministic() -> None:
    first = NORMALIZER.normalize_payload(_record())
    second = NORMALIZER.normalize_payload(_record())
    assert first == second
    assert list(first.fields.items()) == list(second.fields.items())


def test_normalize_accepts_raw_record_payload() -> None:
    raw = RawRecord(
        source="genomeai-reference",
        source_id="REF:1001",
        payload={
            "record_id": "REF:1001",
            "symbol": "TP53",
            "name": "Tumor protein p53",
        },
    )
    entity = NORMALIZER.normalize(raw)
    assert entity.entity_id == "REF:1001"


@pytest.mark.parametrize(
    "payload",
    [
        {"symbol": "X", "name": "n"},
        {"record_id": "", "symbol": "X", "name": "n"},
        {"record_id": "R", "symbol": "", "name": "n"},
    ],
)
def test_invalid_external_data_is_rejected(payload: dict[str, str]) -> None:
    with pytest.raises(NormalizationError):
        NORMALIZER.normalize(RawRecord(source="s", source_id="r", payload=payload))


def test_non_object_payload_rejected() -> None:
    with pytest.raises(NormalizationError):
        NORMALIZER.normalize(RawRecord(source="s", source_id="r", payload=[1, 2]))
