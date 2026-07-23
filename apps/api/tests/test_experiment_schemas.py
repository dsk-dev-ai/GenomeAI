from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.experiment import (
    ExperimentCreate,
    ExperimentResponse,
    ExperimentUpdate,
)
from pydantic import ValidationError


def test_experiment_create_valid() -> None:
    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq of tumor samples",
        experiment_type="RNA-seq",
    )
    assert data.experiment_id == "EXP-001"
    assert data.experiment_name == "RNA-seq of tumor samples"
    assert data.experiment_type == "RNA-seq"
    assert data.platform is None
    assert data.technology is None
    assert data.status is None
    assert data.organism is None
    assert data.laboratory is None
    assert data.researcher is None
    assert data.sample_id is None
    assert data.genome_id is None
    assert data.description is None


def test_experiment_create_with_all_fields() -> None:
    sample_id = uuid.uuid4()
    genome_id = uuid.uuid4()
    data = ExperimentCreate(
        experiment_id="EXP-001",
        experiment_name="RNA-seq of tumor samples",
        experiment_type="RNA-seq",
        platform="Illumina NovaSeq",
        technology="paired-end",
        status="completed",
        organism="Homo sapiens",
        laboratory="Genomics Lab",
        researcher="Dr. Smith",
        sample_id=sample_id,
        genome_id=genome_id,
        description="RNA-seq experiment",
    )
    assert data.experiment_id == "EXP-001"
    assert data.platform == "Illumina NovaSeq"
    assert data.sample_id == sample_id
    assert data.genome_id == genome_id


def test_experiment_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate()


def test_experiment_create_missing_experiment_id() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(experiment_name="RNA-seq")


def test_experiment_create_missing_experiment_name() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(experiment_id="EXP-001")


def test_experiment_create_experiment_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="E" * 101,
            experiment_name="RNA-seq",
        )


def test_experiment_create_experiment_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="E" * 256,
        )


def test_experiment_create_experiment_type_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            experiment_type="E" * 101,
        )


def test_experiment_create_platform_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            platform="P" * 101,
        )


def test_experiment_create_technology_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            technology="T" * 101,
        )


def test_experiment_create_status_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            status="S" * 51,
        )


def test_experiment_create_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            organism="O" * 256,
        )


def test_experiment_create_laboratory_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            laboratory="L" * 256,
        )


def test_experiment_create_researcher_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentCreate(
            experiment_id="EXP-001",
            experiment_name="RNA-seq",
            researcher="R" * 256,
        )


def test_experiment_update_empty() -> None:
    data = ExperimentUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_experiment_update_partial() -> None:
    data = ExperimentUpdate(experiment_name="WGS experiment")
    assert data.experiment_name == "WGS experiment"
    assert data.experiment_id is None


def test_experiment_update_all_fields() -> None:
    sample_id = uuid.uuid4()
    genome_id = uuid.uuid4()
    data = ExperimentUpdate(
        experiment_id="EXP-002",
        experiment_name="WGS experiment",
        experiment_type="WGS",
        platform="PacBio",
        technology="long-read",
        status="running",
        organism="Homo sapiens",
        laboratory="Sequencing Lab",
        researcher="Dr. Jones",
        sample_id=sample_id,
        genome_id=genome_id,
        description="Updated experiment",
    )
    assert data.experiment_id == "EXP-002"
    assert data.sample_id == sample_id
    assert data.genome_id == genome_id


def test_experiment_update_null_experiment_id() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(experiment_id=None)


def test_experiment_update_null_experiment_name() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(experiment_name=None)


def test_experiment_update_experiment_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(experiment_id="E" * 101)


def test_experiment_update_experiment_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(experiment_name="E" * 256)


def test_experiment_update_experiment_type_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(experiment_type="E" * 101)


def test_experiment_update_platform_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(platform="P" * 101)


def test_experiment_update_technology_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(technology="T" * 101)


def test_experiment_update_status_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(status="S" * 51)


def test_experiment_update_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(organism="O" * 256)


def test_experiment_update_laboratory_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(laboratory="L" * 256)


def test_experiment_update_researcher_too_long() -> None:
    with pytest.raises(ValidationError):
        ExperimentUpdate(researcher="R" * 256)


def test_experiment_response_from_attributes() -> None:
    now = datetime.now(UTC)
    experiment_id = uuid.uuid4()
    data = ExperimentResponse.model_validate(
        {
            "id": experiment_id,
            "experiment_id": "EXP-001",
            "experiment_name": "RNA-seq of tumor samples",
            "experiment_type": "RNA-seq",
            "platform": "Illumina NovaSeq",
            "technology": "paired-end",
            "status": "completed",
            "organism": "Homo sapiens",
            "laboratory": "Genomics Lab",
            "researcher": "Dr. Smith",
            "sample_id": None,
            "genome_id": None,
            "description": "RNA-seq experiment",
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == experiment_id
    assert data.experiment_id == "EXP-001"
    assert data.created_at == now
    assert data.updated_at == now


def test_experiment_response_from_orm() -> None:
    from genomeai_api.models.experiment import Experiment

    experiment = Experiment(
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    experiment.id = uuid.uuid4()
    now = datetime.now(UTC)
    experiment.created_at = now
    experiment.updated_at = now

    response = ExperimentResponse.model_validate(experiment)
    assert response.experiment_id == "EXP-001"
    assert response.experiment_name == "RNA-seq"
