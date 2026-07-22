from __future__ import annotations

import uuid

from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome


def test_gene_has_foreign_key_to_genome() -> None:
    genome_id = uuid.uuid4()
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
        genome_id=genome_id,
    )
    assert gene.genome_id == genome_id


def test_gene_genome_id_is_optional() -> None:
    gene = Gene(
        id=uuid.uuid4(),
        gene_id="ENSG00000139618",
        gene_name="TP53",
        chromosome="17",
    )
    assert gene.genome_id is None


def test_gene_genome_id_column_is_fk() -> None:
    col = Gene.__table__.columns["genome_id"]
    assert len(col.foreign_keys) == 1
    fk = next(iter(col.foreign_keys))
    assert fk.column.table.name == "genomes"
    assert fk.column.name == "id"


def test_gene_fk_does_not_affect_genome() -> None:
    genome = Genome(
        id=uuid.uuid4(),
        accession="GCF_000001405.40",
        organism="Homo sapiens",
    )
    assert hasattr(genome, "accession")
    assert "Gene" not in type(genome).__name__
