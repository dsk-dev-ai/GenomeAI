from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.sample import Sample


def test_sample_inherits_base() -> None:
    assert issubclass(Sample, Base)


def test_sample_table_name() -> None:
    assert Sample.__tablename__ == "samples"


def test_sample_id_column() -> None:
    col = Sample.__table__.columns["id"]
    assert col.primary_key


def test_sample_sample_id_column() -> None:
    col = Sample.__table__.columns["sample_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 100
    assert col.index is True


def test_sample_sample_name_column() -> None:
    col = Sample.__table__.columns["sample_name"]
    assert col.nullable is False
    assert col.type.length == 255


def test_sample_organism_column() -> None:
    col = Sample.__table__.columns["organism"]
    assert col.nullable is False
    assert col.type.length == 255


def test_sample_tissue_column() -> None:
    col = Sample.__table__.columns["tissue"]
    assert col.nullable is True
    assert col.type.length == 255


def test_sample_cell_type_column() -> None:
    col = Sample.__table__.columns["cell_type"]
    assert col.nullable is True
    assert col.type.length == 255


def test_sample_disease_column() -> None:
    col = Sample.__table__.columns["disease"]
    assert col.nullable is True
    assert col.type.length == 255


def test_sample_phenotype_column() -> None:
    col = Sample.__table__.columns["phenotype"]
    assert col.nullable is True
    assert col.type.length == 255


def test_sample_sex_column() -> None:
    col = Sample.__table__.columns["sex"]
    assert col.nullable is True
    assert col.type.length == 20


def test_sample_age_column() -> None:
    col = Sample.__table__.columns["age"]
    assert col.nullable is True
    assert col.type.length == 50


def test_sample_genome_id_column() -> None:
    col = Sample.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_sample_description_column() -> None:
    col = Sample.__table__.columns["description"]
    assert col.nullable is True


def test_sample_created_at_column() -> None:
    col = Sample.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_sample_updated_at_column() -> None:
    col = Sample.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_sample_instantiation() -> None:
    sample = Sample(
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
        tissue="Brain",
        cell_type="Neuron",
        disease="Alzheimer's",
        phenotype="Control",
        sex="Male",
        age="65 years",
        description="A brain sample",
    )
    assert sample.sample_id == "SMP001"
    assert sample.sample_name == "Sample 1"
    assert sample.organism == "Homo sapiens"
    assert sample.tissue == "Brain"
    assert sample.cell_type == "Neuron"
    assert sample.disease == "Alzheimer's"
    assert sample.phenotype == "Control"
    assert sample.sex == "Male"
    assert sample.age == "65 years"
    assert sample.description == "A brain sample"


def test_sample_id_type() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    assert isinstance(sample.id, uuid.UUID)


def test_sample_timestamps_are_server_default() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    assert sample.created_at is None
    assert sample.updated_at is None


def test_sample_optional_fields_default_none() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    assert sample.tissue is None
    assert sample.cell_type is None
    assert sample.disease is None
    assert sample.phenotype is None
    assert sample.sex is None
    assert sample.age is None
    assert sample.genome_id is None
    assert sample.description is None


def test_sample_repr() -> None:
    sample = Sample(
        id=uuid.uuid4(),
        sample_id="SMP001",
        sample_name="Sample 1",
        organism="Homo sapiens",
    )
    assert "Sample" in repr(sample)
