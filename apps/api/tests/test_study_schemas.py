from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from genomeai_api.schemas.study import (
    StudyCreate,
    StudyResponse,
    StudyUpdate,
)
from pydantic import ValidationError


def test_study_create_valid() -> None:
    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
        study_type="cohort",
    )
    assert data.study_id == "STU-001"
    assert data.study_name == "Cancer study"
    assert data.study_type == "cohort"
    assert data.title is None
    assert data.description is None
    assert data.organism is None
    assert data.institution is None
    assert data.principal_investigator is None
    assert data.publication is None
    assert data.doi is None
    assert data.start_date is None
    assert data.end_date is None
    assert data.status is None
    assert data.genome_id is None
    assert data.dataset_id is None


def test_study_create_with_all_fields() -> None:
    genome_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    data = StudyCreate(
        study_id="STU-001",
        study_name="Cancer study",
        study_type="cohort",
        title="The Cancer Genome Atlas",
        description="Comprehensive analysis",
        organism="Homo sapiens",
        institution="TCGA",
        principal_investigator="Dr. Collins",
        publication="Nature 2023",
        doi="10.1038/example",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        status="completed",
        genome_id=genome_id,
        dataset_id=dataset_id,
    )
    assert data.study_id == "STU-001"
    assert data.start_date == date(2020, 1, 1)
    assert data.end_date == date(2023, 12, 31)
    assert data.genome_id == genome_id
    assert data.dataset_id == dataset_id


def test_study_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        StudyCreate()


def test_study_create_missing_study_id() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(study_name="Cancer study")


def test_study_create_missing_study_name() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(study_id="STU-001")


def test_study_create_study_id_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="S" * 101,
            study_name="Cancer study",
        )


def test_study_create_study_name_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="S" * 256,
        )


def test_study_create_study_type_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            study_type="T" * 101,
        )


def test_study_create_title_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            title="T" * 501,
        )


def test_study_create_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            organism="O" * 256,
        )


def test_study_create_institution_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            institution="I" * 256,
        )


def test_study_create_pi_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            principal_investigator="P" * 256,
        )


def test_study_create_publication_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            publication="P" * 501,
        )


def test_study_create_doi_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            doi="D" * 101,
        )


def test_study_create_status_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyCreate(
            study_id="STU-001",
            study_name="Cancer study",
            status="S" * 51,
        )


def test_study_update_empty() -> None:
    data = StudyUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_study_update_partial() -> None:
    data = StudyUpdate(study_name="Updated study")
    assert data.study_name == "Updated study"
    assert data.study_id is None


def test_study_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    data = StudyUpdate(
        study_id="STU-002",
        study_name="Updated study",
        study_type="case-control",
        title="Updated title",
        description="Updated description",
        organism="Mus musculus",
        institution="Updated Lab",
        principal_investigator="Dr. Jones",
        publication="Cell 2024",
        doi="10.1038/updated",
        start_date=date(2021, 1, 1),
        end_date=date(2024, 12, 31),
        status="ongoing",
        genome_id=genome_id,
        dataset_id=dataset_id,
    )
    assert data.study_id == "STU-002"
    assert data.genome_id == genome_id
    assert data.dataset_id == dataset_id


def test_study_update_null_study_id() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(study_id=None)


def test_study_update_null_study_name() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(study_name=None)


def test_study_update_study_id_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(study_id="S" * 101)


def test_study_update_study_name_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(study_name="S" * 256)


def test_study_update_study_type_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(study_type="T" * 101)


def test_study_update_title_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(title="T" * 501)


def test_study_update_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(organism="O" * 256)


def test_study_update_institution_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(institution="I" * 256)


def test_study_update_pi_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(principal_investigator="P" * 256)


def test_study_update_publication_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(publication="P" * 501)


def test_study_update_doi_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(doi="D" * 101)


def test_study_update_status_too_long() -> None:
    with pytest.raises(ValidationError):
        StudyUpdate(status="S" * 51)


def test_study_response_from_attributes() -> None:
    now = datetime.now(UTC)
    study_id = uuid.uuid4()
    data = StudyResponse.model_validate(
        {
            "id": study_id,
            "study_id": "STU-001",
            "study_name": "Cancer study",
            "study_type": "cohort",
            "title": "The Cancer Genome Atlas",
            "description": "Comprehensive analysis",
            "organism": "Homo sapiens",
            "institution": "TCGA",
            "principal_investigator": "Dr. Collins",
            "publication": "Nature 2023",
            "doi": "10.1038/example",
            "start_date": None,
            "end_date": None,
            "status": "completed",
            "genome_id": None,
            "dataset_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == study_id
    assert data.study_id == "STU-001"
    assert data.created_at == now
    assert data.updated_at == now


def test_study_response_from_orm() -> None:
    from genomeai_api.models.study import Study

    study = Study(
        study_id="STU-001",
        study_name="Cancer study",
    )
    study.id = uuid.uuid4()
    now = datetime.now(UTC)
    study.created_at = now
    study.updated_at = now

    response = StudyResponse.model_validate(study)
    assert response.study_id == "STU-001"
    assert response.study_name == "Cancer study"
