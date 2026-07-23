from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from genomeai_api.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from pydantic import ValidationError


def test_project_create_valid() -> None:
    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
    )
    assert data.project_id == "PRJ-001"
    assert data.project_name == "Genome project"
    assert data.title is None
    assert data.description is None
    assert data.organization is None
    assert data.owner is None
    assert data.principal_investigator is None
    assert data.status is None
    assert data.start_date is None
    assert data.end_date is None
    assert data.genome_id is None
    assert data.study_id is None


def test_project_create_with_all_fields() -> None:
    genome_id = uuid.uuid4()
    study_id = uuid.uuid4()
    data = ProjectCreate(
        project_id="PRJ-001",
        project_name="Genome project",
        title="1000 Genomes",
        description="Large-scale sequencing",
        organization="Wellcome Trust",
        owner="Dr. Stevens",
        principal_investigator="Dr. Collins",
        status="active",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        genome_id=genome_id,
        study_id=study_id,
    )
    assert data.project_id == "PRJ-001"
    assert data.start_date == date(2020, 1, 1)
    assert data.end_date == date(2023, 12, 31)
    assert data.genome_id == genome_id
    assert data.study_id == study_id


def test_project_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate()


def test_project_create_missing_project_id() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(project_name="Genome project")


def test_project_create_missing_project_name() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(project_id="PRJ-001")


def test_project_create_project_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="P" * 101,
            project_name="Genome project",
        )


def test_project_create_project_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="P" * 256,
        )


def test_project_create_title_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="Genome project",
            title="T" * 501,
        )


def test_project_create_organization_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="Genome project",
            organization="O" * 256,
        )


def test_project_create_owner_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="Genome project",
            owner="O" * 256,
        )


def test_project_create_pi_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="Genome project",
            principal_investigator="P" * 256,
        )


def test_project_create_status_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(
            project_id="PRJ-001",
            project_name="Genome project",
            status="S" * 51,
        )


def test_project_update_empty() -> None:
    data = ProjectUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_project_update_partial() -> None:
    data = ProjectUpdate(project_name="Updated project")
    assert data.project_name == "Updated project"
    assert data.project_id is None


def test_project_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    study_id = uuid.uuid4()
    data = ProjectUpdate(
        project_id="PRJ-002",
        project_name="Updated project",
        title="Updated title",
        description="Updated description",
        organization="Updated Org",
        owner="Dr. Jones",
        principal_investigator="Dr. Smith",
        status="completed",
        start_date=date(2021, 1, 1),
        end_date=date(2024, 12, 31),
        genome_id=genome_id,
        study_id=study_id,
    )
    assert data.project_id == "PRJ-002"
    assert data.genome_id == genome_id
    assert data.study_id == study_id


def test_project_update_null_project_id() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(project_id=None)


def test_project_update_null_project_name() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(project_name=None)


def test_project_update_project_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(project_id="P" * 101)


def test_project_update_project_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(project_name="P" * 256)


def test_project_update_title_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(title="T" * 501)


def test_project_update_organization_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(organization="O" * 256)


def test_project_update_owner_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(owner="O" * 256)


def test_project_update_pi_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(principal_investigator="P" * 256)


def test_project_update_status_too_long() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(status="S" * 51)


def test_project_response_from_attributes() -> None:
    now = datetime.now(UTC)
    project_id = uuid.uuid4()
    data = ProjectResponse.model_validate(
        {
            "id": project_id,
            "project_id": "PRJ-001",
            "project_name": "Genome project",
            "title": "1000 Genomes",
            "description": "Large-scale sequencing",
            "organization": "Wellcome Trust",
            "owner": "Dr. Stevens",
            "principal_investigator": "Dr. Collins",
            "status": "active",
            "start_date": None,
            "end_date": None,
            "genome_id": None,
            "study_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == project_id
    assert data.project_id == "PRJ-001"
    assert data.created_at == now
    assert data.updated_at == now


def test_project_response_from_orm() -> None:
    from genomeai_api.models.project import Project

    project = Project(
        project_id="PRJ-001",
        project_name="Genome project",
    )
    project.id = uuid.uuid4()
    now = datetime.now(UTC)
    project.created_at = now
    project.updated_at = now

    response = ProjectResponse.model_validate(project)
    assert response.project_id == "PRJ-001"
    assert response.project_name == "Genome project"
