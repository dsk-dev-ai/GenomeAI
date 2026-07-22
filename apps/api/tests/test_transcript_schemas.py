from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.transcript import (
    TranscriptCreate,
    TranscriptResponse,
    TranscriptUpdate,
)
from pydantic import ValidationError


def test_transcript_create_valid() -> None:
    data = TranscriptCreate(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
        transcript_type="protein_coding",
    )
    assert data.transcript_id == "ENST00000269305"
    assert data.transcript_name == "TP53-201"
    assert data.chromosome == "17"
    assert data.transcript_type == "protein_coding"
    assert data.strand is None
    assert data.start_position is None
    assert data.end_position is None
    assert data.length is None
    assert data.genome_id is None
    assert data.gene_id is None
    assert data.variant_id is None
    assert data.description is None


def test_transcript_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate()


def test_transcript_create_missing_transcript_id() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(transcript_name="TP53-201", chromosome="17")


def test_transcript_create_missing_transcript_name() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(transcript_id="ENST00000269305", chromosome="17")


def test_transcript_create_missing_chromosome() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="ENST00000269305",
            transcript_name="TP53-201",
        )


def test_transcript_create_transcript_id_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="T" * 51,
            transcript_name="TP53-201",
            chromosome="17",
        )


def test_transcript_create_transcript_name_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="ENST00000269305",
            transcript_name="T" * 256,
            chromosome="17",
        )


def test_transcript_create_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="ENST00000269305",
            transcript_name="TP53-201",
            chromosome="C" * 11,
        )


def test_transcript_create_transcript_type_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="ENST00000269305",
            transcript_name="TP53-201",
            chromosome="17",
            transcript_type="T" * 51,
        )


def test_transcript_create_strand_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptCreate(
            transcript_id="ENST00000269305",
            transcript_name="TP53-201",
            chromosome="17",
            strand="AB",
        )


def test_transcript_update_empty() -> None:
    data = TranscriptUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_transcript_update_partial() -> None:
    data = TranscriptUpdate(chromosome="X")
    assert data.chromosome == "X"
    assert data.transcript_id is None
    assert data.transcript_name is None


def test_transcript_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    gene_id = uuid.uuid4()
    variant_id = uuid.uuid4()
    data = TranscriptUpdate(
        transcript_id="ENST00000420229",
        transcript_name="TP53-202",
        transcript_type="protein_coding",
        chromosome="17",
        strand="-",
        start_position=7661779,
        end_position=7687538,
        length=25759,
        genome_id=genome_id,
        gene_id=gene_id,
        variant_id=variant_id,
        description="Updated transcript",
    )
    assert data.transcript_id == "ENST00000420229"
    assert data.genome_id == genome_id
    assert data.gene_id == gene_id
    assert data.variant_id == variant_id


def test_transcript_update_transcript_id_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptUpdate(transcript_id="T" * 51)


def test_transcript_update_transcript_name_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptUpdate(transcript_name="T" * 256)


def test_transcript_update_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptUpdate(chromosome="C" * 11)


def test_transcript_update_transcript_type_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptUpdate(transcript_type="T" * 51)


def test_transcript_update_strand_too_long() -> None:
    with pytest.raises(ValidationError):
        TranscriptUpdate(strand="ABC")


def test_transcript_response_from_attributes() -> None:
    now = datetime.now(UTC)
    transcript_id = uuid.uuid4()
    data = TranscriptResponse.model_validate(
        {
            "id": transcript_id,
            "transcript_id": "ENST00000269305",
            "transcript_name": "TP53-201",
            "transcript_type": "protein_coding",
            "chromosome": "17",
            "strand": "+",
            "start_position": 7661779,
            "end_position": 7687538,
            "length": 25759,
            "genome_id": None,
            "gene_id": None,
            "variant_id": None,
            "description": "TP53 transcript",
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == transcript_id
    assert data.transcript_id == "ENST00000269305"
    assert data.created_at == now
    assert data.updated_at == now


def test_transcript_response_from_orm() -> None:
    from genomeai_api.models.transcript import Transcript

    transcript = Transcript(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    transcript.id = uuid.uuid4()
    now = datetime.now(UTC)
    transcript.created_at = now
    transcript.updated_at = now

    response = TranscriptResponse.model_validate(transcript)
    assert response.transcript_id == "ENST00000269305"
    assert response.transcript_name == "TP53-201"
    assert response.chromosome == "17"
