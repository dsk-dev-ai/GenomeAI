from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.protein import Protein
from sqlalchemy import Integer, String, Text


def test_protein_inherits_base() -> None:
    assert issubclass(Protein, Base)


def test_protein_table_name() -> None:
    assert Protein.__tablename__ == "proteins"


def test_protein_id_column() -> None:
    col = Protein.__table__.columns["id"]
    assert col.primary_key


def test_protein_protein_id_column() -> None:
    col = Protein.__table__.columns["protein_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 50
    assert col.index is True


def test_protein_protein_name_column() -> None:
    col = Protein.__table__.columns["protein_name"]
    assert col.nullable is False
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_protein_symbol_column() -> None:
    col = Protein.__table__.columns["symbol"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50


def test_protein_accession_column() -> None:
    col = Protein.__table__.columns["accession"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 50
    assert col.index is True


def test_protein_sequence_column() -> None:
    col = Protein.__table__.columns["sequence"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_protein_length_column() -> None:
    col = Protein.__table__.columns["length"]
    assert col.nullable is True
    assert isinstance(col.type, Integer)


def test_protein_molecular_weight_column() -> None:
    col = Protein.__table__.columns["molecular_weight"]
    assert col.nullable is True


def test_protein_organism_column() -> None:
    col = Protein.__table__.columns["organism"]
    assert col.nullable is True
    assert isinstance(col.type, String)
    assert col.type.length == 255


def test_protein_function_column() -> None:
    col = Protein.__table__.columns["function"]
    assert col.nullable is True
    assert isinstance(col.type, Text)


def test_protein_gene_id_column() -> None:
    col = Protein.__table__.columns["gene_id"]
    assert col.nullable is True
    assert col.index is True


def test_protein_transcript_id_column() -> None:
    col = Protein.__table__.columns["transcript_id"]
    assert col.nullable is True
    assert col.index is True


def test_protein_genome_id_column() -> None:
    col = Protein.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_protein_description_column() -> None:
    col = Protein.__table__.columns["description"]
    assert col.nullable is True


def test_protein_created_at_column() -> None:
    col = Protein.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_protein_updated_at_column() -> None:
    col = Protein.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_protein_instantiation() -> None:
    protein = Protein(
        protein_id="P04637",
        protein_name="Cellular tumor antigen p53",
        symbol="TP53",
        accession="P04637",
        sequence="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAM",
        length=393,
        molecular_weight=43653.0,
        organism="Homo sapiens",
        function="Tumor suppressor protein",
        description="TP53 tumor suppressor",
        gene_id=uuid.uuid4(),
        transcript_id=uuid.uuid4(),
        genome_id=uuid.uuid4(),
    )
    assert protein.protein_id == "P04637"
    assert protein.protein_name == "Cellular tumor antigen p53"
    assert protein.symbol == "TP53"
    assert protein.accession == "P04637"
    assert protein.sequence == "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAM"
    assert protein.length == 393
    assert protein.molecular_weight == 43653.0
    assert protein.organism == "Homo sapiens"
    assert protein.function == "Tumor suppressor protein"


def test_protein_id_type() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert isinstance(protein.id, uuid.UUID)


def test_protein_timestamps_are_server_default() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert protein.created_at is None
    assert protein.updated_at is None


def test_protein_optional_fields_default_none() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert protein.symbol is None
    assert protein.accession is None
    assert protein.sequence is None
    assert protein.length is None
    assert protein.molecular_weight is None
    assert protein.organism is None
    assert protein.function is None
    assert protein.gene_id is None
    assert protein.transcript_id is None
    assert protein.genome_id is None
    assert protein.description is None


def test_protein_repr() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert "Protein" in repr(protein)
