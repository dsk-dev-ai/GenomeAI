from __future__ import annotations

import uuid

from genomeai_api.models.genome import Genome
from genomeai_api.models.project import Project
from genomeai_api.models.study import Study


def test_project_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
        genome_id=genome_id,
    )
    assert project.genome_id == genome_id


def test_project_genome_id_is_optional() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert project.genome_id is None


def test_project_has_foreign_key_to_study() -> None:
    study_id = uuid.uuid4()
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
        study_id=study_id,
    )
    assert project.study_id == study_id


def test_project_study_id_is_optional() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert project.study_id is None


def test_project_genome_id_column_is_fk() -> None:
    col = Project.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_project_study_id_column_is_fk() -> None:
    col = Project.__table__.columns["study_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "studies"
    assert fk.column.name == "id"


def test_project_has_relationship_to_genome() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert hasattr(project, "genome")


def test_project_has_relationship_to_study() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert hasattr(project, "study")


def test_genome_has_relationship_to_projects() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "projects")


def test_study_has_relationship_to_projects() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert hasattr(study, "projects")


def test_project_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Project" not in type(genome).__name__


def test_project_fk_does_not_affect_study() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert hasattr(study, "study_id")
    assert "Project" not in type(study).__name__
