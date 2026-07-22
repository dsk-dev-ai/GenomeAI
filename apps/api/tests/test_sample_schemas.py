from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.sample import SampleCreate, SampleResponse, SampleUpdate
from pydantic import ValidationError


def test_sample_create_valid() -> None:
    data = SampleCreate(
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
        tissue="Brain",
    )
    assert data.sample_id == "SMP001"
    assert data.sample_name == "Sample 1"
    assert data.organism == "Homo sapiens"
    assert data.tissue == "Brain"
    assert data.cell_type is None
    assert data.disease is None
    assert data.phenotype is None
    assert data.sex is None
    assert data.age is None
    assert data.genome_id is None
    assert data.description is None


def test_sample_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        SampleCreate()


def test_sample_create_missing_sample_id() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(sample_name="Sample 1", organism="Homo sapiens")


def test_sample_create_missing_sample_name() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(sample_id="SMP001", organism="Homo sapiens")


def test_sample_create_missing_organism() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(sample_id="SMP001", sample_name="Sample 1")


def test_sample_create_sample_id_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="S" * 101,
            sample_name="Sample 1",
            organism="Homo sapiens",
        )


def test_sample_create_sample_name_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="N" * 256,
            organism="Homo sapiens",
        )


def test_sample_create_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="O" * 256,
        )


def test_sample_create_tissue_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            tissue="T" * 256,
        )


def test_sample_create_cell_type_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            cell_type="C" * 256,
        )


def test_sample_create_disease_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            disease="D" * 256,
        )


def test_sample_create_phenotype_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            phenotype="P" * 256,
        )


def test_sample_create_sex_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            sex="S" * 21,
        )


def test_sample_create_age_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleCreate(
            sample_id="SMP001",
            sample_name="Sample 1",
            organism="Homo sapiens",
            age="A" * 51,
        )


def test_sample_update_empty() -> None:
    data = SampleUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_sample_update_partial() -> None:
    data = SampleUpdate(organism="Mus musculus")
    assert data.organism == "Mus musculus"
    assert data.sample_id is None
    assert data.sample_name is None


def test_sample_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    data = SampleUpdate(
        sample_id="SMP002",
        sample_name="Sample 2",
        organism="Mus musculus",
        tissue="Liver",
        cell_type="Hepatocyte",
        disease="None",
        phenotype="Control",
        sex="Female",
        age="10 weeks",
        genome_id=genome_id,
        description="A mouse liver sample",
    )
    assert data.sample_id == "SMP002"
    assert data.genome_id == genome_id


def test_sample_update_sample_id_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(sample_id="S" * 101)


def test_sample_update_sample_name_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(sample_name="N" * 256)


def test_sample_update_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(organism="O" * 256)


def test_sample_update_tissue_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(tissue="T" * 256)


def test_sample_update_cell_type_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(cell_type="C" * 256)


def test_sample_update_disease_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(disease="D" * 256)


def test_sample_update_phenotype_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(phenotype="P" * 256)


def test_sample_update_sex_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(sex="S" * 21)


def test_sample_update_age_too_long() -> None:
    with pytest.raises(ValidationError):
        SampleUpdate(age="A" * 51)


def test_sample_response_from_attributes() -> None:
    now = datetime.now(UTC)
    sample_id = uuid.uuid4()
    data = SampleResponse.model_validate(
        {
            "id": sample_id,
            "sample_id": "SMP001",
            "sample_name": "Sample 1",
            "organism": "Homo sapiens",
            "tissue": "Brain",
            "cell_type": None,
            "disease": None,
            "phenotype": None,
            "sex": None,
            "age": None,
            "genome_id": None,
            "description": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == sample_id
    assert data.sample_id == "SMP001"
    assert data.created_at == now
    assert data.updated_at == now


def test_sample_response_from_orm() -> None:
    from genomeai_api.models.sample import Sample

    sample = Sample(
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    sample.id = uuid.uuid4()
    now = datetime.now(UTC)
    sample.created_at = now
    sample.updated_at = now

    response = SampleResponse.model_validate(sample)
    assert response.sample_id == "SMP001"
    assert response.organism == "Homo sapiens"
