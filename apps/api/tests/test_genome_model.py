from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.genome import Genome


def test_genome_inherits_base() -> None:
    assert issubclass(Genome, Base)


def test_genome_table_name() -> None:
    assert Genome.__tablename__ == "genomes"


def test_genome_columns() -> None:
    cols = {c.name: c for c in Genome.__table__.columns}
    assert cols["id"].primary_key
    assert cols["accession"].unique is True
    assert cols["accession"].nullable is False
    assert cols["organism"].nullable is False
    assert cols["assembly"].nullable is True
    assert cols["source"].nullable is True
    assert cols["description"].nullable is True
    assert cols["created_at"].nullable is False
    assert cols["updated_at"].nullable is False


def test_genome_instantiation() -> None:
    genome = Genome(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
        assembly="GRCh38.p14",
        source="NCBI",
        description="Human reference genome",
    )
    assert genome.accession == "GCF_000001405.40"
    assert genome.organism == "Homo sapiens"
    assert genome.assembly == "GRCh38.p14"
    assert genome.source == "NCBI"
    assert genome.description == "Human reference genome"


def test_genome_auto_fields() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert isinstance(genome.id, uuid.UUID)
    assert genome.created_at is None  # server_default
    assert genome.updated_at is None  # server_default


def test_genome_optional_fields_default_none() -> None:
    genome = Genome(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert genome.assembly is None
    assert genome.source is None
    assert genome.description is None


def test_genome_repr() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert "Genome" in repr(genome)
