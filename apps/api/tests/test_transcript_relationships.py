from __future__ import annotations

import uuid

from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome
from genomeai_api.models.transcript import Transcript
from genomeai_api.models.variant import Variant


def test_transcript_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
        genome_id=genome_id,
    )
    assert transcript.genome_id == genome_id


def test_transcript_genome_id_is_optional() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert transcript.genome_id is None


def test_transcript_has_foreign_key_to_gene() -> None:
    gene_id = uuid.uuid4()
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
        gene_id=gene_id,
    )
    assert transcript.gene_id == gene_id


def test_transcript_gene_id_is_optional() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert transcript.gene_id is None


def test_transcript_has_foreign_key_to_variant() -> None:
    variant_id = uuid.uuid4()
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
        variant_id=variant_id,
    )
    assert transcript.variant_id == variant_id


def test_transcript_variant_id_is_optional() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert transcript.variant_id is None


def test_transcript_genome_id_column_is_fk() -> None:
    col = Transcript.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_transcript_gene_id_column_is_fk() -> None:
    col = Transcript.__table__.columns["gene_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genes"
    assert fk.column.name == "id"


def test_transcript_variant_id_column_is_fk() -> None:
    col = Transcript.__table__.columns["variant_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "variants"
    assert fk.column.name == "id"


def test_transcript_has_relationship_to_genome() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert hasattr(transcript, "genome")


def test_transcript_has_relationship_to_gene() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert hasattr(transcript, "gene")


def test_transcript_has_relationship_to_variant() -> None:
    transcript = Transcript(
        id=uuid.uuid4(),
        transcript_id="ENST00000269305",
        transcript_name="TP53-201",
        chromosome="17",
    )
    assert hasattr(transcript, "variant")


def test_genome_has_relationship_to_transcripts() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "transcripts")


def test_gene_has_relationship_to_transcripts() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert hasattr(gene, "transcripts")


def test_variant_has_relationship_to_transcripts() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert hasattr(variant, "transcripts")


def test_transcript_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Transcript" not in type(genome).__name__


def test_transcript_fk_does_not_affect_gene() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert hasattr(gene, "gene_id")
    assert "Transcript" not in type(gene).__name__


def test_transcript_fk_does_not_affect_variant() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert hasattr(variant, "variant_id")
    assert "Transcript" not in type(variant).__name__
