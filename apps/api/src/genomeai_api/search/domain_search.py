from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import DeclarativeBase

from genomeai_api.models.dataset import Dataset
from genomeai_api.models.experiment import Experiment
from genomeai_api.models.gene import Gene
from genomeai_api.models.genome import Genome
from genomeai_api.models.project import Project
from genomeai_api.models.protein import Protein
from genomeai_api.models.sample import Sample
from genomeai_api.models.study import Study
from genomeai_api.models.transcript import Transcript
from genomeai_api.models.variant import Variant

WeightType = Literal["A", "B", "C", "D"]


@dataclass(frozen=True)
class DomainSearchConfig:
    model: type[DeclarativeBase]
    search_fields: list[str]
    fts_fields: list[str]
    fts_weights: list[WeightType] | None = None
    fts_config: str = "english"
    suggestion_field: str | None = None
    default_sort_field: str | None = None
    default_sort_order: str = "asc"
    has_coordinate_search: bool = False
    coordinate_chromosome_column: str = "chromosome"
    coordinate_start_column: str = "start_position"
    coordinate_end_column: str = "end_position"


GENE_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Gene,
    search_fields=["gene_id", "gene_name", "description"],
    fts_fields=["gene_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="gene_name",
    default_sort_field="gene_name",
    has_coordinate_search=True,
    coordinate_chromosome_column="chromosome",
    coordinate_start_column="start_position",
    coordinate_end_column="end_position",
)

PROTEIN_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Protein,
    search_fields=["protein_id", "protein_name", "accession", "symbol", "description"],
    fts_fields=["protein_name", "description", "function"],
    fts_weights=["A", "B", "C"],
    suggestion_field="protein_name",
    default_sort_field="protein_name",
)

VARIANT_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Variant,
    search_fields=["variant_id", "chromosome", "ref", "alt", "description"],
    fts_fields=["variant_id", "ref", "alt", "description"],
    fts_weights=["A", "B", "B", "C"],
    suggestion_field="variant_id",
    default_sort_field="variant_id",
    has_coordinate_search=True,
    coordinate_chromosome_column="chromosome",
    coordinate_start_column="position",
    coordinate_end_column="position",
)

TRANSCRIPT_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Transcript,
    search_fields=["transcript_id", "transcript_name", "description"],
    fts_fields=["transcript_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="transcript_name",
    default_sort_field="transcript_name",
    has_coordinate_search=True,
    coordinate_chromosome_column="chromosome",
    coordinate_start_column="start_position",
    coordinate_end_column="end_position",
)

GENOME_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Genome,
    search_fields=["accession", "organism", "assembly", "description"],
    fts_fields=["accession", "organism", "assembly", "description"],
    fts_weights=["A", "B", "B", "C"],
    suggestion_field="accession",
    default_sort_field="accession",
)

STUDY_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Study,
    search_fields=["study_id", "study_name", "title", "description"],
    fts_fields=["title", "description"],
    fts_weights=["A", "B"],
    suggestion_field="study_name",
    default_sort_field="study_name",
)

SAMPLE_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Sample,
    search_fields=["sample_id", "sample_name", "description"],
    fts_fields=["sample_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="sample_name",
    default_sort_field="sample_name",
)

DATASET_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Dataset,
    search_fields=["dataset_id", "dataset_name", "description"],
    fts_fields=["dataset_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="dataset_name",
    default_sort_field="dataset_name",
)

EXPERIMENT_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Experiment,
    search_fields=["experiment_id", "experiment_name", "description"],
    fts_fields=["experiment_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="experiment_name",
    default_sort_field="experiment_name",
)

PROJECT_SEARCH: DomainSearchConfig = DomainSearchConfig(
    model=Project,
    search_fields=["project_id", "project_name", "description"],
    fts_fields=["project_name", "description"],
    fts_weights=["A", "B"],
    suggestion_field="project_name",
    default_sort_field="project_name",
)

DOMAIN_SEARCH_CONFIGS: dict[str, DomainSearchConfig] = {
    "gene": GENE_SEARCH,
    "protein": PROTEIN_SEARCH,
    "variant": VARIANT_SEARCH,
    "transcript": TRANSCRIPT_SEARCH,
    "genome": GENOME_SEARCH,
    "study": STUDY_SEARCH,
    "sample": SAMPLE_SEARCH,
    "dataset": DATASET_SEARCH,
    "experiment": EXPERIMENT_SEARCH,
    "project": PROJECT_SEARCH,
}
