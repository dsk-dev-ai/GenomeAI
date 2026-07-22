from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.variant import Variant


def test_variant_inherits_base() -> None:
    assert issubclass(Variant, Base)


def test_variant_table_name() -> None:
    assert Variant.__tablename__ == "variants"


def test_variant_id_column() -> None:
    col = Variant.__table__.columns["id"]
    assert col.primary_key


def test_variant_variant_id_column() -> None:
    col = Variant.__table__.columns["variant_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 255
    assert col.index is True


def test_variant_chromosome_column() -> None:
    col = Variant.__table__.columns["chromosome"]
    assert col.nullable is False
    assert col.type.length == 10


def test_variant_position_column() -> None:
    col = Variant.__table__.columns["position"]
    assert col.nullable is False


def test_variant_ref_column() -> None:
    col = Variant.__table__.columns["ref"]
    assert col.nullable is False
    assert col.type.length == 500


def test_variant_alt_column() -> None:
    col = Variant.__table__.columns["alt"]
    assert col.nullable is False
    assert col.type.length == 500


def test_variant_type_column() -> None:
    col = Variant.__table__.columns["type"]
    assert col.nullable is True
    assert col.type.length == 50


def test_variant_quality_column() -> None:
    col = Variant.__table__.columns["quality"]
    assert col.nullable is True


def test_variant_filter_status_column() -> None:
    col = Variant.__table__.columns["filter_status"]
    assert col.nullable is True
    assert col.type.length == 50


def test_variant_genome_id_column() -> None:
    col = Variant.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_variant_gene_id_column() -> None:
    col = Variant.__table__.columns["gene_id"]
    assert col.nullable is True
    assert col.index is True


def test_variant_description_column() -> None:
    col = Variant.__table__.columns["description"]
    assert col.nullable is True


def test_variant_created_at_column() -> None:
    col = Variant.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_variant_updated_at_column() -> None:
    col = Variant.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_variant_instantiation() -> None:
    variant = Variant(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
        type="snv",
        quality=999.5,
        filter_status="PASS",
        description="A somatic SNV in TP53",
        genome_id=uuid.uuid4(),
        gene_id=uuid.uuid4(),
    )
    assert variant.variant_id == "chr17_7674220_G_A"
    assert variant.chromosome == "17"
    assert variant.position == 7674220
    assert variant.ref == "G"
    assert variant.alt == "A"
    assert variant.type == "snv"
    assert variant.quality == 999.5
    assert variant.filter_status == "PASS"
    assert variant.description == "A somatic SNV in TP53"


def test_variant_id_type() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert isinstance(variant.id, uuid.UUID)


def test_variant_timestamps_are_server_default() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert variant.created_at is None
    assert variant.updated_at is None


def test_variant_optional_fields_default_none() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert variant.type is None
    assert variant.quality is None
    assert variant.filter_status is None
    assert variant.genome_id is None
    assert variant.gene_id is None
    assert variant.description is None


def test_variant_repr() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert "Variant" in repr(variant)
