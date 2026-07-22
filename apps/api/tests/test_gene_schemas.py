from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.gene import GeneCreate, GeneResponse, GeneUpdate
from pydantic import ValidationError


def test_gene_create_valid() -> None:
    data = GeneCreate(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
        biotype="protein_coding",
    )
    assert data.gene_id == "ENSG00000139618"
    assert data.gene_name == "TP53"
    assert data.chromosome == "17"
    assert data.biotype == "protein_coding"
    assert data.strand is None
    assert data.start_position is None
    assert data.end_position is None
    assert data.description is None
    assert data.genome_id is None


def test_gene_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        GeneCreate()


def test_gene_create_missing_gene_id() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(gene_name="TP53", chromosome="17")


def test_gene_create_missing_gene_name() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(gene_id="ENSG00000139618", chromosome="17")


def test_gene_create_missing_chromosome() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(gene_id="ENSG00000139618", gene_name="TP53")


def test_gene_create_gene_id_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(
            gene_id="E" * 51,
            gene_name="TP53",
            chromosome="17",
        )


def test_gene_create_gene_name_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(
            gene_id="ENSG00000139618",
            gene_name="N" * 256,
            chromosome="17",
        )


def test_gene_create_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(
            gene_id="ENSG00000139618",
            gene_name="TP53",
            chromosome="C" * 11,
        )


def test_gene_create_strand_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(
            gene_id="ENSG00000139618",
            gene_name="TP53",
            chromosome="17",
            strand="++",
        )


def test_gene_create_biotype_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneCreate(
            gene_id="ENSG00000139618",
            gene_name="TP53",
            chromosome="17",
            biotype="B" * 51,
        )


def test_gene_update_empty() -> None:
    data = GeneUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_gene_update_partial() -> None:
    data = GeneUpdate(gene_name="BRCA1")
    assert data.gene_name == "BRCA1"
    assert data.gene_id is None
    assert data.chromosome is None


def test_gene_update_all_fields() -> None:
    genome_id = uuid.uuid4()
    data = GeneUpdate(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
        strand="-",
        start_position=7661779,
        end_position=7687538,
        biotype="protein_coding",
        description="Tumor protein p53",
        genome_id=genome_id,
    )
    assert data.gene_id == "ENSG00000139618"
    assert data.genome_id == genome_id


def test_gene_update_gene_id_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneUpdate(gene_id="E" * 51)


def test_gene_update_gene_name_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneUpdate(gene_name="N" * 256)


def test_gene_update_chromosome_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneUpdate(chromosome="C" * 11)


def test_gene_update_strand_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneUpdate(strand="++")


def test_gene_update_biotype_too_long() -> None:
    with pytest.raises(ValidationError):
        GeneUpdate(biotype="B" * 51)


def test_gene_response_from_attributes() -> None:
    now = datetime.now(UTC)
    gene_id = uuid.uuid4()
    data = GeneResponse.model_validate(
        {
            "id": gene_id,
            "gene_id": "ENSG00000139618",
            "gene_name": "TP53",
            "chromosome": "17",
            "strand": "-",
            "start_position": 7661779,
            "end_position": 7687538,
            "biotype": "protein_coding",
            "description": "Tumor protein p53",
            "genome_id": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == gene_id
    assert data.gene_id == "ENSG00000139618"
    assert data.created_at == now
    assert data.updated_at == now


def test_gene_response_from_orm() -> None:
    from genomeai_api.models.gene import Gene

    gene = Gene(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    gene.id = uuid.uuid4()
    now = datetime.now(UTC)
    gene.created_at = now
    gene.updated_at = now

    response = GeneResponse.model_validate(gene)
    assert response.gene_id == "ENSG00000139618"
    assert response.gene_name == "TP53"
