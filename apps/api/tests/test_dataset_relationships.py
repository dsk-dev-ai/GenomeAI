from __future__ import annotations

import uuid

from genomeai_api.models.dataset import Dataset
from genomeai_api.models.experiment import Experiment
from genomeai_api.models.genome import Genome


def test_dataset_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
        genome_id=genome_id,
    )
    assert dataset.genome_id == genome_id


def test_dataset_genome_id_is_optional() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert dataset.genome_id is None


def test_dataset_has_foreign_key_to_experiment() -> None:
    experiment_id = uuid.uuid4()
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
        experiment_id=experiment_id,
    )
    assert dataset.experiment_id == experiment_id


def test_dataset_experiment_id_is_optional() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert dataset.experiment_id is None


def test_dataset_genome_id_column_is_fk() -> None:
    col = Dataset.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_dataset_experiment_id_column_is_fk() -> None:
    col = Dataset.__table__.columns["experiment_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "experiments"
    assert fk.column.name == "id"


def test_dataset_has_relationship_to_genome() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert hasattr(dataset, "genome")


def test_dataset_has_relationship_to_experiment() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert hasattr(dataset, "experiment")


def test_genome_has_relationship_to_datasets() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "datasets")


def test_experiment_has_relationship_to_datasets() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert hasattr(experiment, "datasets")


def test_dataset_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Dataset" not in type(genome).__name__


def test_dataset_fk_does_not_affect_experiment() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert hasattr(experiment, "experiment_id")
    assert "Dataset" not in type(experiment).__name__
