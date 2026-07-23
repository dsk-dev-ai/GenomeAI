from __future__ import annotations

import uuid

from genomeai_api.models.dataset import Dataset
from genomeai_api.models.genome import Genome
from genomeai_api.models.study import Study


def test_study_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
        genome_id=genome_id,
    )
    assert study.genome_id == genome_id


def test_study_genome_id_is_optional() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert study.genome_id is None


def test_study_has_foreign_key_to_dataset() -> None:
    dataset_id = uuid.uuid4()
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
        dataset_id=dataset_id,
    )
    assert study.dataset_id == dataset_id


def test_study_dataset_id_is_optional() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert study.dataset_id is None


def test_study_genome_id_column_is_fk() -> None:
    col = Study.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_study_dataset_id_column_is_fk() -> None:
    col = Study.__table__.columns["dataset_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "datasets"
    assert fk.column.name == "id"


def test_study_has_relationship_to_genome() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert hasattr(study, "genome")


def test_study_has_relationship_to_dataset() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert hasattr(study, "dataset")


def test_genome_has_relationship_to_studies() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "studies")


def test_dataset_has_relationship_to_studies() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert hasattr(dataset, "studies")


def test_study_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Study" not in type(genome).__name__


def test_study_fk_does_not_affect_dataset() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert hasattr(dataset, "dataset_id")
    assert "Study" not in type(dataset).__name__
