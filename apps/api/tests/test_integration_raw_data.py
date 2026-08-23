from __future__ import annotations

from genomeai_api.integration.raw_data import (
    ProvenanceRecord,
    RawRecord,
    checksum_bytes,
    checksum_json,
)


def test_checksum_is_deterministic_sha256() -> None:
    first = checksum_bytes(b"payload")
    second = checksum_bytes(b"payload")
    assert first == second
    assert len(first) == 64
    assert checksum_bytes(b"other") != first


def test_checksum_json_ignores_key_order() -> None:
    assert checksum_json({"a": 1, "b": 2}) == checksum_json({"b": 2, "a": 1})


def test_raw_record_with_checksum_hashes_payload() -> None:
    record = RawRecord(
        source="genomeai-reference",
        source_id="REF:1",
        source_version="2",
        retrieved_at="2026-08-23T00:00:00+00:00",
        payload={"id": 1},
    )
    stamped = record.with_checksum()
    assert stamped.payload_sha256 == checksum_json({"id": 1})
    # Original stays untouched (frozen boundary).
    assert record.payload_sha256 is None


def test_raw_record_without_payload_has_no_checksum() -> None:
    record = RawRecord(source="s", source_id="r")
    assert record.with_checksum().payload_sha256 is None


def test_provenance_record_defaults_are_filled() -> None:
    record = ProvenanceRecord(source="s", source_record_id="r", checksum="abc")
    assert record.retrieved_at is not None
    assert record.ingested_at is not None
    # No release is ever fabricated.
    assert record.source_release is None


def test_raw_record_preserves_source_identity() -> None:
    record = RawRecord(source="ncbi", source_id="GENE:1", source_version="p38")
    assert record.source == "ncbi"
    assert record.source_id == "GENE:1"
    assert record.source_version == "p38"
