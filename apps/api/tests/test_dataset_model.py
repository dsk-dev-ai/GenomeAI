from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.dataset import Dataset
from sqlalchemy import BigInteger, Boolean, Integer, String, Text


def test_dataset_inherits_base() -> None:
    assert issubclass(Dataset, Base)


def test_dataset_table_name() -> None:
    assert Dataset.__tablename__ == "datasets"


def test_dataset_id_column() -> None:
    col = Dataset.__table__.columns["id"]
    assert col.primary_key


def test_dataset_dataset_id_column() -> None:
    col = Dataset.__table__.columns["dataset_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 100
    assert col.index is True


def test_dataset_dataset_name_column() -> None:
    col = Dataset.__table__.columns["dataset_name"]
    assert col.nullable is False
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_dataset_dataset_type_column() -> None:
    col = Dataset.__table__.columns["dataset_type"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_dataset_source_column() -> None:
    col = Dataset.__table__.columns["source"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_dataset_organism_column() -> None:
    col = Dataset.__table__.columns["organism"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_dataset_version_column() -> None:
    col = Dataset.__table__.columns["version"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50


def test_dataset_description_column() -> None:
    col = Dataset.__table__.columns["description"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_dataset_sample_count_column() -> None:
    col = Dataset.__table__.columns["sample_count"]
    assert col.nullable is True
    assert isinstance(col.type, Integer)


def test_dataset_file_count_column() -> None:
    col = Dataset.__table__.columns["file_count"]
    assert col.nullable is True
    assert isinstance(col.type, Integer)


def test_dataset_size_bytes_column() -> None:
    col = Dataset.__table__.columns["size_bytes"]
    assert col.nullable is True
    assert isinstance(col.type, BigInteger)


def test_dataset_is_public_column() -> None:
    col = Dataset.__table__.columns["is_public"]
    assert col.nullable is True
    assert isinstance(col.type, Boolean)


def test_dataset_genome_id_column() -> None:
    col = Dataset.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_dataset_experiment_id_column() -> None:
    col = Dataset.__table__.columns["experiment_id"]
    assert col.nullable is True
    assert col.index is True


def test_dataset_created_at_column() -> None:
    col = Dataset.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_dataset_updated_at_column() -> None:
    col = Dataset.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_dataset_instantiation() -> None:
    dataset = Dataset(
        dataset_id="DS-001",
        dataset_name="RNA-seq tumor expression data",
        dataset_type="expression",
        source="TCGA",
        organism="Homo sapiens",
        version="v1.0",
        description="RNA-seq expression data from tumor samples",
        sample_count=100,
        file_count=5,
        size_bytes=1073741824,
        is_public=True,
        genome_id=uuid.uuid4(),
        experiment_id=uuid.uuid4(),
    )
    assert dataset.dataset_id == "DS-001"
    assert dataset.dataset_name == "RNA-seq tumor expression data"
    assert dataset.dataset_type == "expression"
    assert dataset.source == "TCGA"
    assert dataset.organism == "Homo sapiens"
    assert dataset.version == "v1.0"
    assert dataset.sample_count == 100
    assert dataset.file_count == 5
    assert dataset.size_bytes == 1073741824
    assert dataset.is_public is True


def test_dataset_id_type() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert isinstance(dataset.id, uuid.UUID)


def test_dataset_timestamps_are_server_default() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert dataset.created_at is None
    assert dataset.updated_at is None


def test_dataset_optional_fields_default_none() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert dataset.dataset_type is None
    assert dataset.source is None
    assert dataset.organism is None
    assert dataset.version is None
    assert dataset.description is None
    assert dataset.sample_count is None
    assert dataset.file_count is None
    assert dataset.size_bytes is None
    assert dataset.is_public is None
    assert dataset.genome_id is None
    assert dataset.experiment_id is None


def test_dataset_repr() -> None:
    dataset = Dataset(
        id=uuid.uuid4(),
        dataset_id="DS-001",
        dataset_name="RNA-seq data",
    )
    assert "Dataset" in repr(dataset)
