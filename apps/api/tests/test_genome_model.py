from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.genome import Genome


def test_genome_inherits_base() -> None:
    assert issubclass(Genome, Base)


def test_genome_table_name() -> None:
    assert Genome.__tablename__ == "genomes"


def test_genome_id_column() -> None:
    col = Genome.__table__.columns["id"]
    assert col.primary_key


def test_genome_accession_column() -> None:
    col = Genome.__table__.columns["accession"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 50
    assert col.index is True


def test_genome_organism_column() -> None:
    col = Genome.__table__.columns["organism"]
    assert col.nullable is False
    assert col.type.length == 255


def test_genome_assembly_column() -> None:
    col = Genome.__table__.columns["assembly"]
    assert col.nullable is True
    assert col.type.length == 100


def test_genome_source_column() -> None:
    col = Genome.__table__.columns["source"]
    assert col.nullable is True
    assert col.type.length == 100


def test_genome_description_column() -> None:
    col = Genome.__table__.columns["description"]
    assert col.nullable is True


def test_genome_created_at_column() -> None:
    col = Genome.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_genome_updated_at_column() -> None:
    col = Genome.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


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


def test_genome_id_type() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert isinstance(genome.id, uuid.UUID)


def test_genome_timestamps_are_server_default() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert genome.created_at is None
    assert genome.updated_at is None


def test_genome_optional_fields_default_none() -> None:
    genome = Genome(
        id=uuid.uuid4(),
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
