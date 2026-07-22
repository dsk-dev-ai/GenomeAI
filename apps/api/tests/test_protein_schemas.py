from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from genomeai_api.schemas.protein import (
    ProteinCreate,
    ProteinResponse,
    ProteinUpdate,
)
from pydantic import ValidationError


def test_protein_create_valid() -> None:
    data = ProteinCreate(
        protein_id="P04637",
        protein_name="Cellular tumor antigen p53",
        symbol="TP53",
    )
    assert data.protein_id == "P04637"
    assert data.protein_name == "Cellular tumor antigen p53"
    assert data.symbol == "TP53"
    assert data.accession is None
    assert data.sequence is None
    assert data.length is None
    assert data.molecular_weight is None
    assert data.organism is None
    assert data.function is None
    assert data.gene_id is None
    assert data.transcript_id is None
    assert data.genome_id is None
    assert data.description is None


def test_protein_create_with_all_fields() -> None:
    gene_id = uuid.uuid4()
    transcript_id = uuid.uuid4()
    genome_id = uuid.uuid4()
    data = ProteinCreate(
        protein_id="P04637",
        protein_name="Cellular tumor antigen p53",
        symbol="TP53",
        accession="P04637",
        sequence="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAM",
        length=393,
        molecular_weight=43653.0,
        organism="Homo sapiens",
        function="Tumor suppressor",
        gene_id=gene_id,
        transcript_id=transcript_id,
        genome_id=genome_id,
        description="TP53 tumor suppressor",
    )
    assert data.length == 393
    assert data.molecular_weight == 43653.0
    assert data.gene_id == gene_id
    assert data.transcript_id == transcript_id
    assert data.genome_id == genome_id


def test_protein_create_required_fields() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate()


def test_protein_create_missing_protein_id() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(protein_name="p53")


def test_protein_create_missing_protein_name() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(protein_id="P04637")


def test_protein_create_protein_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P" * 51,
            protein_name="p53",
        )


def test_protein_create_protein_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="P" * 256,
        )


def test_protein_create_symbol_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="p53",
            symbol="S" * 51,
        )


def test_protein_create_accession_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="p53",
            accession="A" * 51,
        )


def test_protein_create_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="p53",
            organism="O" * 256,
        )


def test_protein_create_negative_length() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="p53",
            length=-1,
        )


def test_protein_create_negative_molecular_weight() -> None:
    with pytest.raises(ValidationError):
        ProteinCreate(
            protein_id="P04637",
            protein_name="p53",
            molecular_weight=-1.0,
        )


def test_protein_create_zero_length() -> None:
    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
        length=0,
    )
    assert data.length == 0


def test_protein_create_zero_molecular_weight() -> None:
    data = ProteinCreate(
        protein_id="P04637",
        protein_name="p53",
        molecular_weight=0.0,
    )
    assert data.molecular_weight == 0.0


def test_protein_update_empty() -> None:
    data = ProteinUpdate()
    assert data.model_dump(exclude_unset=True) == {}


def test_protein_update_partial() -> None:
    data = ProteinUpdate(protein_name="p53 (updated)")
    assert data.protein_name == "p53 (updated)"
    assert data.protein_id is None


def test_protein_update_all_fields() -> None:
    gene_id = uuid.uuid4()
    transcript_id = uuid.uuid4()
    genome_id = uuid.uuid4()
    data = ProteinUpdate(
        protein_id="P04638",
        protein_name="p63",
        symbol="TP63",
        accession="Q9H3D4",
        sequence="MIRAVEMSFFS",
        length=100,
        molecular_weight=11000.0,
        organism="Homo sapiens",
        function="Transcription factor",
        gene_id=gene_id,
        transcript_id=transcript_id,
        genome_id=genome_id,
        description="Updated protein",
    )
    assert data.protein_id == "P04638"
    assert data.gene_id == gene_id
    assert data.transcript_id == transcript_id
    assert data.genome_id == genome_id


def test_protein_update_protein_id_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(protein_id="P" * 51)


def test_protein_update_protein_name_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(protein_name="P" * 256)


def test_protein_update_symbol_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(symbol="S" * 51)


def test_protein_update_accession_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(accession="A" * 51)


def test_protein_update_organism_too_long() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(organism="O" * 256)


def test_protein_update_negative_length() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(length=-1)


def test_protein_update_negative_molecular_weight() -> None:
    with pytest.raises(ValidationError):
        ProteinUpdate(molecular_weight=-1.0)


def test_protein_update_zero_length() -> None:
    data = ProteinUpdate(length=0)
    assert data.length == 0


def test_protein_response_from_attributes() -> None:
    now = datetime.now(UTC)
    protein_id = uuid.uuid4()
    data = ProteinResponse.model_validate(
        {
            "id": protein_id,
            "protein_id": "P04637",
            "protein_name": "Cellular tumor antigen p53",
            "symbol": "TP53",
            "accession": "P04637",
            "sequence": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAM",
            "length": 393,
            "molecular_weight": 43653.0,
            "organism": "Homo sapiens",
            "function": "Tumor suppressor",
            "gene_id": None,
            "transcript_id": None,
            "genome_id": None,
            "description": "TP53 tumor suppressor",
            "created_at": now,
            "updated_at": now,
        }
    )
    assert data.id == protein_id
    assert data.protein_id == "P04637"
    assert data.created_at == now
    assert data.updated_at == now


def test_protein_response_from_orm() -> None:
    from genomeai_api.models.protein import Protein

    protein = Protein(
        protein_id="P04637",
        protein_name="Cellular tumor antigen p53",
    )
    protein.id = uuid.uuid4()
    now = datetime.now(UTC)
    protein.created_at = now
    protein.updated_at = now

    response = ProteinResponse.model_validate(protein)
    assert response.protein_id == "P04637"
    assert response.protein_name == "Cellular tumor antigen p53"
