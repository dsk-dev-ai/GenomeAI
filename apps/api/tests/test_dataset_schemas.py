from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetUpdate,
)
from pydantic import ValidationError


def test_dataset_create_valid() -> None:
    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq expression data",
        dataset_type="expression",
    )
    assert data.dataset_id == "DS-001"
    assert data.dataset_name == "RNA-seq expression data"
    assert data.dataset_type == "expression"
    assert data.source is None
    assert data.organism is None
    assert data.version is None
    assert data.description is None
    assert data.sample_count is None
    assert data.file_count is None
    assert data.size_bytes is None
    assert data.is_public is None
    assert data.genome_id is None
    assert data.experiment_id is None


def test_dataset_create_with_all_fields() -> None:
    genome_id = uuid.uuid4()
    experiment_id = uuid.uuid4()
    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq expression data",
        dataset_type="expression",
        source="TCGA",
        organism="Homo sapiens",
        version="v1.0",
        description="Expression data",
        sample_count=100,
        file_count=5,
        size_bytes=1073741824,
        is_public=True,
        genome_id=genome_id,
        experiment_id=experiment_id,
    )
    assert data.dataset_id == "DS-001"
    assert data.sample_count == 100
    assert data.file_count == 5
    assert data.size_bytes == 1073741824
    assert data.is_public is True
    assert data.genome_id == genome_id
    assert data.experiment_id == experiment_id


def test_dataset_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate()


def test_dataset_create_missing_dataset_id() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(dataset_name="RNA-seq data")


def test_dataset_create_missing_dataset_name() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(dataset_id="DS-001")


def test_dataset_create_dataset_id_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="D" * 101,
            dataset_name="RNA-seq data",
        )


def test_dataset_create_dataset_name_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="D" * 256,
        )


def test_dataset_create_dataset_type_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            dataset_type="D" * 101,
        )


def test_dataset_create_source_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            source="S" * 256,
        )


def test_dataset_create_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            organism="O" * 256,
        )


def test_dataset_create_version_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            version="V" * 51,
        )


def test_dataset_create_negative_sample_count() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            sample_count=-1,
        )


def test_dataset_create_negative_file_count() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            file_count=-1,
        )


def test_dataset_create_negative_size_bytes() -> None:
    with pytest.raises(ValidationError):
        DatasetCreate(
            dataset_id="DS-001",
            dataset_name="RNA-seq data",
            size_bytes=-1,
        )


def test_dataset_create_zero_counts() -> None:
    data = DatasetCreate(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
        sample_count=0,
        file_count=0,
        size_bytes=0,
    )
    assert data.sample_count == 0
    assert data.file_count == 0
    assert data.size_bytes == 0


def test_dataset_update_empty() -> None:
    data = DatasetUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_dataset_update_partial() -> None:
    data = DatasetUpdate(dataset_name="WGS expression data")
    assert data.dataset_name == "WGS expression data"
    assert data.dataset_id is None


def test_dataset_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    experiment_id = uuid.uuid4()
    data = DatasetUpdate(
        dataset_id="DS-002",
        dataset_name="WGS data",
        dataset_type="variant",
        source="ENCODE",
        organism="Homo sapiens",
        version="v2.0",
        description="Updated dataset",
        sample_count=50,
        file_count=3,
        size_bytes=536870912,
        is_public=False,
        genome_id=genome_id,
        experiment_id=experiment_id,
    )
    assert data.dataset_id == "DS-002"
    assert data.genome_id == genome_id
    assert data.experiment_id == experiment_id


def test_dataset_update_null_dataset_id() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(dataset_id=None)


def test_dataset_update_null_dataset_name() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(dataset_name=None)


def test_dataset_update_dataset_id_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(dataset_id="D" * 101)


def test_dataset_update_dataset_name_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(dataset_name="D" * 256)


def test_dataset_update_dataset_type_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(dataset_type="D" * 101)


def test_dataset_update_source_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(source="S" * 256)


def test_dataset_update_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(organism="O" * 256)


def test_dataset_update_version_too_long() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(version="V" * 51)


def test_dataset_update_negative_sample_count() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(sample_count=-1)


def test_dataset_update_negative_file_count() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(file_count=-1)


def test_dataset_update_negative_size_bytes() -> None:
    with pytest.raises(ValidationError):
        DatasetUpdate(size_bytes=-1)


def test_dataset_update_zero_counts() -> None:
    data = DatasetUpdate(sample_count=0, file_count=0, size_bytes=0)
    assert data.sample_count == 0


def test_dataset_response_from_attributes() -> None:
    now = datetime.now(UTC)
    dataset_id = uuid.uuid4()
    data = DatasetResponse.model_validate(
        {
            "id": dataset_id,
            "dataset_id": "DS-001",
            "dataset_name": "RNA-seq expression data",
            "dataset_type": "expression",
            "source": "TCGA",
            "organism": "Homo sapiens",
            "version": "v1.0",
            "description": "Expression data",
            "sample_count": 100,
            "file_count": 5,
            "size_bytes": 1073741824,
            "is_public": True,
            "genome_id": None,
            "experiment_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == dataset_id
    assert data.dataset_id == "DS-001"
    assert data.created_at == now
    assert data.updated_at == now


def test_dataset_response_from_orm() -> None:
    from genomeai_api.models.dataset import Dataset

    dataset = Dataset(
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    dataset.id = uuid.uuid4()
    now = datetime.now(UTC)
    dataset.created_at = now
    dataset.updated_at = now

    response = DatasetResponse.model_validate(dataset)
    assert response.dataset_id == "DS-001"
    assert response.dataset_name == "RNA-seq data"
