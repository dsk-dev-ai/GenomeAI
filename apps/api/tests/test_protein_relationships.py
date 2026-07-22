from __future__ import annotations

import uuid

from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome
from genomeai_api.models.protein import Protein
from genomeai_api.models.transcript import Transcript
from genomeai_api.models.variant import Variant


def test_protein_has_foreign_key_to_gene() -> None:
    gene_id = uuid.uuid4()
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
        gene_id=gene_id,
    )
    assert protein.gene_id == gene_id


def test_protein_gene_id_is_optional() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert protein.gene_id is None


def test_protein_has_foreign_key_to_transcript() -> None:
    transcript_id = uuid.uuid4()
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
        transcript_id=transcript_id,
    )
    assert protein.transcript_id == transcript_id


def test_protein_transcript_id_is_optional() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert protein.transcript_id is None


def test_protein_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
        genome_id=genome_id,
    )
    assert protein.genome_id == genome_id


def test_protein_genome_id_is_optional() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert protein.genome_id is None


def test_protein_gene_id_column_is_fk() -> None:
    col = Protein.__table__.columns["gene_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genes"
    assert fk.column.name == "id"


def test_protein_transcript_id_column_is_fk() -> None:
    col = Protein.__table__.columns["transcript_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "transcripts"
    assert fk.column.name == "id"


def test_protein_genome_id_column_is_fk() -> None:
    col = Protein.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_protein_has_relationship_to_gene() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert hasattr(protein, "gene")


def test_protein_has_relationship_to_transcript() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert hasattr(protein, "transcript")


def test_protein_has_relationship_to_genome() -> None:
    protein = Protein(
        id=uuid.uuid4(),
        protein_id="P04637",
        protein_name="p53",
    )
    assert hasattr(protein, "genome")


def test_gene_has_relationship_to_proteins() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert hasattr(gene, "proteins")


def test_transcript_has_relationship_to_proteins() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert hasattr(transcript, "proteins")


def test_genome_has_relationship_to_proteins() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "proteins")


def test_protein_fk_does_not_affect_gene() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert hasattr(gene, "gene_id")
    assert "Protein" not in type(gene).__name__


def test_protein_fk_does_not_affect_transcript() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert hasattr(transcript, "transcript_id")
    assert "Protein" not in type(transcript).__name__


def test_protein_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Protein" not in type(genome).__name__


def test_protein_fk_does_not_affect_variant() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert hasattr(variant, "variant_id")
    assert "Protein" not in type(variant).__name__
