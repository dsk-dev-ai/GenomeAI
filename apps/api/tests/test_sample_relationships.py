from __future__ import annotations

import uuid

from genomeai_api.models.genome import Genome
from genomeai_api.models.sample import Sample


def test_sample_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
        genome_id=genome_id,
    )
    assert sample.genome_id == genome_id


def test_sample_genome_id_is_optional() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    assert sample.genome_id is None


def test_sample_genome_id_column_is_fk() -> None:
    col = Sample.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_sample_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Sample" not in type(genome).__name__
