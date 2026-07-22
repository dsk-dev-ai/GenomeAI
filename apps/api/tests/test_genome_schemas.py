from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.genome import GenomeCreate, GenomeResponse, GenomeUpdate
from pydantic import ValidationError


def test_genome_create_valid() -> None:
    data = GenomeCreate(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
        assembly="GRCh38.p14",
    )
    assert data.accession == "GCF_000001405.40"
    assert data.organism == "Homo sapiens"
    assert data.assembly == "GRCh38.p14"
    assert data.source is None
    assert data.description is None


def test_genome_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        GenomeCreate()


def test_genome_create_missing_accession() -> None:
    with pytest.raises(ValidationError):
        GenomeCreate(organism="Homo sapiens")


def test_genome_create_missing_organism() -> None:
    with pytest.raises(ValidationError):
        GenomeCreate(accession="GCF_000001405.40")


def test_genome_update_empty() -> None:
    data = GenomeUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_genome_update_partial() -> None:
    data = GenomeUpdate(organism="Mus musculus")
    assert data.organism == "Mus musculus"
    assert data.accession is None
    assert data.assembly is None


def test_genome_update_all_fields() -> None:
    data = GenomeUpdate(
        accession="GCF_000001405.41",
        organism="Homo sapiens",
        assembly="GRCh38.p14",
        source="NCBI",
        description="Updated",
    )
    assert data.accession == "GCF_000001405.41"


def test_genome_response_from_attributes() -> None:
    now = datetime.now(UTC)
    genome_id = uuid.uuid4()
    data = GenomeResponse.model_validate(
        {
            "id": genome_id,
            "accession": "GCF_000001405.40",
            "organism": "Homo sapiens",
            "assembly": "GRCh38.p14",
            "source": "NCBI",
            "description": "Test",
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == genome_id
    assert data.created_at == now
    assert data.updated_at == now


def test_genome_response_from_orm() -> None:
    from genomeai_api.models.genome import Genome

    genome = Genome(
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    genome.id = uuid.uuid4()
    now = datetime.now(UTC)
    genome.created_at = now
    genome.updated_at = now

    response = GenomeResponse.model_validate(genome)
    assert response.accession == "GCF_000001405.40"
    assert response.organism == "Homo sapiens"
