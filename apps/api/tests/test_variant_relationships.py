from __future__ import annotations

import uuid

from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome
from genomeai_api.models.variant import Variant


def test_variant_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
        genome_id=genome_id,
    )
    assert variant.genome_id == genome_id


def test_variant_genome_id_is_optional() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert variant.genome_id is None


def test_variant_has_foreign_key_to_gene() -> None:
    gene_id = uuid.uuid4()
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
        gene_id=gene_id,
    )
    assert variant.gene_id == gene_id


def test_variant_gene_id_is_optional() -> None:
    variant = Variant(
        id=uuid.uuid4(),
        variant_id="chr17_7674220_G_A",
        chromosome="17",
        position=7674220,
        ref="G",
        alt="A",
    )
    assert variant.gene_id is None


def test_variant_genome_id_column_is_fk() -> None:
    col = Variant.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_variant_gene_id_column_is_fk() -> None:
    col = Variant.__table__.columns["gene_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genes"
    assert fk.column.name == "id"


def test_variant_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Variant" not in type(genome).__name__


def test_variant_fk_does_not_affect_gene() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert hasattr(gene, "gene_id")
    assert "Variant" not in type(gene).__name__
