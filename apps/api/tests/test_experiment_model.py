from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.experiment import Experiment
from sqlalchemy import String, Text


def test_experiment_inherits_base() -> None:
    assert issubclass(Experiment, Base)


def test_experiment_table_name() -> None:
    assert Experiment.__tablename__ == "experiments"


def test_experiment_id_column() -> None:
    col = Experiment.__table__.columns["id"]
    assert col.primary_key


def test_experiment_experiment_id_column() -> None:
    col = Experiment.__table__.columns["experiment_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 100
    assert col.index is True


def test_experiment_experiment_name_column() -> None:
    col = Experiment.__table__.columns["experiment_name"]
    assert col.nullable is False
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_experiment_experiment_type_column() -> None:
    col = Experiment.__table__.columns["experiment_type"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_experiment_platform_column() -> None:
    col = Experiment.__table__.columns["platform"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_experiment_technology_column() -> None:
    col = Experiment.__table__.columns["technology"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 100


def test_experiment_status_column() -> None:
    col = Experiment.__table__.columns["status"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50


def test_experiment_organism_column() -> None:
    col = Experiment.__table__.columns["organism"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_experiment_laboratory_column() -> None:
    col = Experiment.__table__.columns["laboratory"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_experiment_researcher_column() -> None:
    col = Experiment.__table__.columns["researcher"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_experiment_sample_id_column() -> None:
    col = Experiment.__table__.columns["sample_id"]
    assert col.nullable is True
    assert col.index is True


def test_experiment_genome_id_column() -> None:
    col = Experiment.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_experiment_description_column() -> None:
    col = Experiment.__table__.columns["description"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_experiment_created_at_column() -> None:
    col = Experiment.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_experiment_updated_at_column() -> None:
    col = Experiment.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_experiment_instantiation() -> None:
    experiment = Experiment(
        experiment_id="EXP-001",
        experiment_name="RNA-seq of tumor samples",
        experiment_type="RNA-seq",
        platform="Illumina NovaSeq",
        technology="paired-end",
        status="completed",
        organism="Homo sapiens",
        laboratory="Genomics Lab",
        researcher="Dr. Smith",
        description="RNA-seq experiment",
        sample_id=uuid.uuid4(),
        genome_id=uuid.uuid4(),
    )
    assert experiment.experiment_id == "EXP-001"
    assert experiment.experiment_name == "RNA-seq of tumor samples"
    assert experiment.experiment_type == "RNA-seq"
    assert experiment.platform == "Illumina NovaSeq"
    assert experiment.technology == "paired-end"
    assert experiment.status == "completed"
    assert experiment.organism == "Homo sapiens"
    assert experiment.laboratory == "Genomics Lab"
    assert experiment.researcher == "Dr. Smith"
    assert experiment.description == "RNA-seq experiment"


def test_experiment_id_type() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert isinstance(experiment.id, uuid.UUID)


def test_experiment_timestamps_are_server_default() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert experiment.created_at is None
    assert experiment.updated_at is None


def test_experiment_optional_fields_default_none() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert experiment.experiment_type is None
    assert experiment.platform is None
    assert experiment.technology is None
    assert experiment.status is None
    assert experiment.organism is None
    assert experiment.laboratory is None
    assert experiment.researcher is None
    assert experiment.sample_id is None
    assert experiment.genome_id is None
    assert experiment.description is None


def test_experiment_repr() -> None:
    experiment = Experiment(
        id=uuid.uuid4(),
        experiment_id="EXP-001",
        experiment_name="RNA-seq",
    )
    assert "Experiment" in repr(experiment)
