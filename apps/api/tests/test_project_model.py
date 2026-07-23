from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.project import Project
from sqlalchemy import Date, String, Text


def test_project_inherits_base() -> None:
    assert issubclass(Project, Base)


def test_project_table_name() -> None:
    assert Project.__tablename__ == "projects"


def test_project_id_column() -> None:
    col = Project.__table__.columns["id"]
    assert col.primary_key


def test_project_project_id_column() -> None:
    col = Project.__table__.columns["project_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 100
    assert col.index is True


def test_project_project_name_column() -> None:
    col = Project.__table__.columns["project_name"]
    assert col.nullable is False
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_project_title_column() -> None:
    col = Project.__table__.columns["title"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 500


def test_project_description_column() -> None:
    col = Project.__table__.columns["description"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_project_organization_column() -> None:
    col = Project.__table__.columns["organization"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_project_owner_column() -> None:
    col = Project.__table__.columns["owner"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_project_principal_investigator_column() -> None:
    col = Project.__table__.columns["principal_investigator"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_project_status_column() -> None:
    col = Project.__table__.columns["status"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50


def test_project_start_date_column() -> None:
    col = Project.__table__.columns["start_date"]
    assert col.nullable is True
    assert isinstance(col.type, Date)


def test_project_end_date_column() -> None:
    col = Project.__table__.columns["end_date"]
    assert col.nullable is True
    assert isinstance(col.type, Date)


def test_project_genome_id_column() -> None:
    col = Project.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_project_study_id_column() -> None:
    col = Project.__table__.columns["study_id"]
    assert col.nullable is True
    assert col.index is True


def test_project_created_at_column() -> None:
    col = Project.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_project_updated_at_column() -> None:
    col = Project.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_project_instantiation() -> None:
    project = Project(
        project_id="PRJ-001",
        project_name="Genome sequencing project",
        title="1000 Genomes Project",
        description="Large-scale genome sequencing",
        organization="Wellcome Trust",
        owner="Dr. Stevens",
        principal_investigator="Dr. Collins",
        status="active",
        genome_id=uuid.uuid4(),
        study_id=uuid.uuid4(),
    )
    assert project.project_id == "PRJ-001"
    assert project.project_name == "Genome sequencing project"
    assert project.title == "1000 Genomes Project"
    assert project.description == "Large-scale genome sequencing"
    assert project.organization == "Wellcome Trust"
    assert project.owner == "Dr. Stevens"
    assert project.principal_investigator == "Dr. Collins"
    assert project.status == "active"


def test_project_id_type() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert isinstance(project.id, uuid.UUID)


def test_project_timestamps_are_server_default() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert project.created_at is None
    assert project.updated_at is None


def test_project_optional_fields_default_none() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert project.title is None
    assert project.description is None
    assert project.organization is None
    assert project.owner is None
    assert project.principal_investigator is None
    assert project.status is None
    assert project.start_date is None
    assert project.end_date is None
    assert project.genome_id is None
    assert project.study_id is None


def test_project_repr() -> None:
    project = Project(
        id=uuid.uuid4(),
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert "Project" in repr(project)
