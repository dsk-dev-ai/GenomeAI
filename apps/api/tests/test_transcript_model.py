from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.transcript import Transcript


def test_transcript_inherits_base() -> None:
    assert issubclass(Transcript, Base)


def test_transcript_table_name() -> None:
    assert Transcript.__tablename__ == "transcripts"


def test_transcript_id_column() -> None:
    col = Transcript.__table__.columns["id"]
    assert col.primary_key


def test_transcript_transcript_id_column() -> None:
    col = Transcript.__table__.columns["transcript_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 50
    assert col.index is True


def test_transcript_transcript_name_column() -> None:
    col = Transcript.__table__.columns["transcript_name"]
    assert col.nullable is False
    assert col.type.length == 255


def test_transcript_transcript_type_column() -> None:
    col = Transcript.__table__.columns["transcript_type"]
    assert col.nullable is True
    assert col.type.length == 50


def test_transcript_chromosome_column() -> None:
    col = Transcript.__table__.columns["chromosome"]
    assert col.nullable is False
    assert col.type.length == 10


def test_transcript_strand_column() -> None:
    col = Transcript.__table__.columns["strand"]
    assert col.nullable is True
    assert col.type.length == 1


def test_transcript_start_position_column() -> None:
    col = Transcript.__table__.columns["start_position"]
    assert col.nullable is True
    assert isinstance(col.type, col.type.__class__)


def test_transcript_end_position_column() -> None:
    col = Transcript.__table__.columns["end_position"]
    assert col.nullable is True


def test_transcript_length_column() -> None:
    col = Transcript.__table__.columns["length"]
    assert col.nullable is True


def test_transcript_genome_id_column() -> None:
    col = Transcript.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_transcript_gene_id_column() -> None:
    col = Transcript.__table__.columns["gene_id"]
    assert col.nullable is True
    assert col.index is True


def test_transcript_variant_id_column() -> None:
    col = Transcript.__table__.columns["variant_id"]
    assert col.nullable is True
    assert col.index is True


def test_transcript_description_column() -> None:
    col = Transcript.__table__.columns["description"]
    assert col.nullable is True


def test_transcript_created_at_column() -> None:
    col = Transcript.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_transcript_updated_at_column() -> None:
    col = Transcript.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_transcript_instantiation() -> None:
    transcript = Transcript(
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        transcript_type="protein_coding",
        chromosome="17",
        strand="+",
        start_position=7661779,
        end_position=7687538,
        length=25759,
        description="TP53 tumor suppressor transcript",
        genome_id=uuid.uuid4(),
        gene_id=uuid.uuid4(),
        variant_id=uuid.uuid4(),
    )
    assert transcript.transcript_id == "ENST00000269305"
    assert transcript.transcript_name == "TP53-201"
    assert transcript.transcript_type == "protein_coding"
    assert transcript.chromosome == "17"
    assert transcript.strand == "+"
    assert transcript.start_position == 7661779
    assert transcript.end_position == 7687538
    assert transcript.length == 25759
    assert transcript.description == "TP53 tumor suppressor transcript"


def test_transcript_id_type() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert isinstance(transcript.id, uuid.UUID)


def test_transcript_timestamps_are_server_default() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert transcript.created_at is None
    assert transcript.updated_at is None


def test_transcript_optional_fields_default_none() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert transcript.transcript_type is None
    assert transcript.strand is None
    assert transcript.start_position is None
    assert transcript.end_position is None
    assert transcript.length is None
    assert transcript.genome_id is None
    assert transcript.gene_id is None
    assert transcript.variant_id is None
    assert transcript.description is None


def test_transcript_repr() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert "Transcript" in repr(transcript)
