from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.variant import VariantCreate, VariantResponse, VariantUpdate
from pydantic import ValidationError


def test_variant_create_valid() -> None:
    data = VariantCreate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
        type="snv",
    )
    assert data.variant_id == "chr17_7674220_G_A"
    assert data.chromosome == "17"
    assert data.position == 7674220
    assert data.ref == "G"
    assert data.alt == "A"
    assert data.type == "snv"
    assert data.quality is None
    assert data.filter_status is None
    assert data.genome_id is None
    assert data.gene_id is None
    assert data.description is None


def test_variant_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        VariantCreate()


def test_variant_create_missing_variant_id() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(chromosome="17", position=7674220, ref="G", alt="A")


def test_variant_create_missing_chromosome() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(variant_id="chr17_7674220_G_A", position=7674220, ref="G", alt="A")


def test_variant_create_missing_position() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(variant_id="chr17_7674220_G_A", chromosome="17", ref="G", alt="A")


def test_variant_create_missing_ref() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(variant_id="chr17_7674220_G_A", chromosome="17", position=7674220, alt="A")


def test_variant_create_missing_alt() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(variant_id="chr17_7674220_G_A", chromosome="17", position=7674220, ref="G")


def test_variant_create_variant_id_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="V" * 256,
            chromosome="17",
            position=7674220,
            ref="G",
            alt="A",
        )


def test_variant_create_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="chr17_7674220_G_A",
            chromosome="C" * 11,
            position=7674220,
            ref="G",
            alt="A",
        )


def test_variant_create_ref_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="chr17_7674220_G_A",
            chromosome="17",
            position=7674220,
            ref="R" * 501,
            alt="A",
        )


def test_variant_create_alt_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="chr17_7674220_G_A",
            chromosome="17",
            position=7674220,
            ref="G",
            alt="A" * 501,
        )


def test_variant_create_position_zero() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="chr17_7674220_G_A",
            chromosome="17",
            position=0,
            ref="G",
            alt="A",
        )


def test_variant_create_type_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantCreate(
            variant_id="chr17_7674220_G_A",
            chromosome="17",
            position=7674220,
            ref="G",
            alt="A",
            type="T" * 51,
        )


def test_variant_update_empty() -> None:
    data = VariantUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_variant_update_partial() -> None:
    data = VariantUpdate(chromosome="X")
    assert data.chromosome == "X"
    assert data.variant_id is None
    assert data.position is None


def test_variant_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    gene_id = uuid.uuid4()
    data = VariantUpdate(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
        type="snv",
        quality=999.5,
        filter_status="PASS",
        genome_id=genome_id,
        gene_id=gene_id,
        description="Updated variant",
    )
    assert data.variant_id == "chr17_7674220_G_A"
    assert data.genome_id == genome_id
    assert data.gene_id == gene_id


def test_variant_update_variant_id_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(variant_id="V" * 256)


def test_variant_update_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(chromosome="C" * 11)


def test_variant_update_ref_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(ref="R" * 501)


def test_variant_update_alt_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(alt="A" * 501)


def test_variant_update_type_too_long() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(type="T" * 51)


def test_variant_update_position_zero() -> None:
    with pytest.raises(ValidationError):
        VariantUpdate(position=0)


def test_variant_response_from_attributes() -> None:
    now = datetime.now(UTC)
    variant_id = uuid.uuid4()
    data = VariantResponse.model_validate(
        {
            "id": variant_id,
            "variant_id": "chr17_7674220_G_A",
            "chromosome": "17",
            "position": 7674220,
            "ref": "G",
            "alt": "A",
            "type": "snv",
            "quality": 999.5,
            "filter_status": "PASS",
            "genome_id": None,
            "gene_id": None,
            "description": "A somatic SNV",
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == variant_id
    assert data.variant_id == "chr17_7674220_G_A"
    assert data.created_at == now
    assert data.updated_at == now


def test_variant_response_from_orm() -> None:
    from genomeai_api.models.variant import Variant

    variant = Variant(
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    variant.id = uuid.uuid4()
    now = datetime.now(UTC)
    variant.created_at = now
    variant.updated_at = now

    response = VariantResponse.model_validate(variant)
    assert response.variant_id == "chr17_7674220_G_A"
    assert response.chromosome == "17"
