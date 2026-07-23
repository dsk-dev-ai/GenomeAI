from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.study import Study
from sqlalchemy import Date, String, Text


def test_study_inherits_base() -> None:
    assert issubclass(Study, Base)


def test_study_table_name() -> None:
    assert Study.__tablename__ == "studies"


def test_study_id_column() -> None:
    col = Study.__table__.columns["id"]
    assert col.primary_key


def test_study_study_id_column() -> None:
    col = Study.__table__.columns["study_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 100
    assert col.index is True


def test_study_study_name_column() -> None:
    col = Study.__table__.columns["study_name"]
    assert col.nullable is False
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_study_study_type_column() -> None:
    col = Study.__table__.columns["study_type"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_study_title_column() -> None:
    col = Study.__table__.columns["title"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 500


def test_study_description_column() -> None:
    col = Study.__table__.columns["description"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_study_organism_column() -> None:
    col = Study.__table__.columns["organism"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_study_institution_column() -> None:
    col = Study.__table__.columns["institution"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_study_principal_investigator_column() -> None:
    col = Study.__table__.columns["principal_investigator"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_study_publication_column() -> None:
    col = Study.__table__.columns["publication"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 500


def test_study_doi_column() -> None:
    col = Study.__table__.columns["doi"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_study_start_date_column() -> None:
    col = Study.__table__.columns["start_date"]
    assert col.nullable is True
    assert isinstance(col.type, Date)


def test_study_end_date_column() -> None:
    col = Study.__table__.columns["end_date"]
    assert col.nullable is True
    assert isinstance(col.type, Date)


def test_study_status_column() -> None:
    col = Study.__table__.columns["status"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50


def test_study_genome_id_column() -> None:
    col = Study.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_study_dataset_id_column() -> None:
    col = Study.__table__.columns["dataset_id"]
    assert col.nullable is True
    assert col.index is True


def test_study_created_at_column() -> None:
    col = Study.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_study_updated_at_column() -> None:
    col = Study.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_study_instantiation() -> None:
    study = Study(
        study_id="STU-001",
        study_name="Cancer genome atlas study",
        study_type="cohort",
        title="The Cancer Genome Atlas",
        description="Comprehensive genomic analysis",
        organism="Homo sapiens",
        institution="TCGA Consortium",
        principal_investigator="Dr. Collins",
        publication="Nature 2023",
        doi="10.1038/example",
        status="completed",
        genome_id=uuid.uuid4(),
        dataset_id=uuid.uuid4(),
    )
    assert study.study_id == "STU-001"
    assert study.study_name == "Cancer genome atlas study"
    assert study.study_type == "cohort"
    assert study.title == "The Cancer Genome Atlas"
    assert study.description == "Comprehensive genomic analysis"
    assert study.organism == "Homo sapiens"
    assert study.institution == "TCGA Consortium"
    assert study.principal_investigator == "Dr. Collins"
    assert study.publication == "Nature 2023"
    assert study.doi == "10.1038/example"
    assert study.status == "completed"


def test_study_id_type() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert isinstance(study.id, uuid.UUID)


def test_study_timestamps_are_server_default() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert study.created_at is None
    assert study.updated_at is None


def test_study_optional_fields_default_none() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert study.study_type is None
    assert study.title is None
    assert study.description is None
    assert study.organism is None
    assert study.institution is None
    assert study.principal_investigator is None
    assert study.publication is None
    assert study.doi is None
    assert study.start_date is None
    assert study.end_date is None
    assert study.status is None
    assert study.genome_id is None
    assert study.dataset_id is None


def test_study_repr() -> None:
    study = Study(
        id=uuid.uuid4(),
        study_id="STU-001",
        study_name="Cancer study",
    )
    assert "Study" in repr(study)
