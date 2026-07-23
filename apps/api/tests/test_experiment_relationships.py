from __future__ import annotations

import uuid

from genomeai_api.models.experiment import Experiment
from genomeai_api.models.genome import Genome
from genomeai_api.models.sample import Sample


def test_experiment_has_foreign_key_to_sample() -> None:
    sample_id = uuid.uuid4()
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
        sample_id=sample_id,
    )
    assert experiment.sample_id == sample_id


def test_experiment_sample_id_is_optional() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert experiment.sample_id is None


def test_experiment_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
        genome_id=genome_id,
    )
    assert experiment.genome_id == genome_id


def test_experiment_genome_id_is_optional() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert experiment.genome_id is None


def test_experiment_sample_id_column_is_fk() -> None:
    col = Experiment.__table__.columns["sample_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "samples"
    assert fk.column.name == "id"


def test_experiment_genome_id_column_is_fk() -> None:
    col = Experiment.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_experiment_has_relationship_to_sample() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert hasattr(experiment, "sample")


def test_experiment_has_relationship_to_genome() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert hasattr(experiment, "genome")


def test_sample_has_relationship_to_experiments() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SAMPLE-001",
        sample_name="Tumor sample",
        organism="Homo sapiens",
    )
    assert hasattr(sample, "experiments")


def test_genome_has_relationship_to_experiments() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "experiments")


def test_experiment_fk_does_not_affect_sample() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SAMPLE-001",
        sample_name="Tumor sample",
        organism="Homo sapiens",
    )
    assert hasattr(sample, "sample_id")
    assert "Experiment" not in type(sample).__name__


def test_experiment_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Experiment" not in type(genome).__name__
