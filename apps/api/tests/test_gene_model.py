from __future__ import annotations

import uuid

from genomeai_api.database.base import Base
from genomeai_api.models.gene import Gene


def test_gene_inherits_base() -> None:
    assert issubclass(Gene, Base)


def test_gene_table_name() -> None:
    assert Gene.__tablename__ == "genes"


def test_gene_id_column() -> None:
    col = Gene.__table__.columns["id"]
    assert col.primary_key


def test_gene_gene_id_column() -> None:
    col = Gene.__table__.columns["gene_id"]
    assert col.unique is True
    assert col.nullable is False
    assert col.type.length == 50
    assert col.index is True


def test_gene_gene_name_column() -> None:
    col = Gene.__table__.columns["gene_name"]
    assert col.nullable is False
    assert col.type.length == 255


def test_gene_chromosome_column() -> None:
    col = Gene.__table__.columns["chromosome"]
    assert col.nullable is False
    assert col.type.length == 10


def test_gene_strand_column() -> None:
    col = Gene.__table__.columns["strand"]
    assert col.nullable is True
    assert col.type.length == 1


def test_gene_start_position_column() -> None:
    col = Gene.__table__.columns["start_position"]
    assert col.nullable is True


def test_gene_end_position_column() -> None:
    col = Gene.__table__.columns["end_position"]
    assert col.nullable is True


def test_gene_biotype_column() -> None:
    col = Gene.__table__.columns["biotype"]
    assert col.nullable is True
    assert col.type.length == 50


def test_gene_description_column() -> None:
    col = Gene.__table__.columns["description"]
    assert col.nullable is True


def test_gene_genome_id_column() -> None:
    col = Gene.__table__.columns["genome_id"]
    assert col.nullable is True
    assert col.index is True


def test_gene_created_at_column() -> None:
    col = Gene.__table__.columns["created_at"]
    assert col.nullable is False
    assert col.type.timezone is True


def test_gene_updated_at_column() -> None:
    col = Gene.__table__.columns["updated_at"]
    assert col.nullable is False
    assert col.type.timezone is True
    assert col.onupdate is not None


def test_gene_instantiation() -> None:
    gene = Gene(
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
        strand="-",
        start_position=7661779,
        end_position=7687538,
        biotype="protein_coding",
        description="Tumor protein p53",
        genome_id=uuid.uuid4(),
    )
    assert gene.gene_id == "ENSG00000139618"
    assert gene.gene_name == "TP53"
    assert gene.chromosome == "17"
    assert gene.strand == "-"
    assert gene.start_position == 7661779
    assert gene.end_position == 7687538
    assert gene.biotype == "protein_coding"
    assert gene.description == "Tumor protein p53"


def test_gene_id_type() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert isinstance(gene.id, uuid.UUID)


def test_gene_timestamps_are_server_default() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert gene.created_at is None
    assert gene.updated_at is None


def test_gene_optional_fields_default_none() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert gene.strand is None
    assert gene.start_position is None
    assert gene.end_position is None
    assert gene.biotype is None
    assert gene.description is None
    assert gene.genome_id is None


def test_gene_repr() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert "Gene" in repr(gene)
