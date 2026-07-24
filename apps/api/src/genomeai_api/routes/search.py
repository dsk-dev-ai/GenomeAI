from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from genomeai_api.dependencies import get_db_session
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
from genomeai_api.schemas.search import SuggestionResponse
from genomeai_api.search.cache import NullCache
from genomeai_api.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])

DOMAIN_MAP: dict[str, type[DeclarativeBase]] = {
    "genome": Genome,
    "sample": Sample,
    "gene": Gene,
    "variant": Variant,
    "transcript": Transcript,
    "protein": Protein,
    "experiment": Experiment,
    "dataset": Dataset,
    "study": Study,
    "project": Project,
}

DEFAULT_FIELDS: dict[str, str] = {
    "genome": "accession",
    "sample": "sample_name",
    "gene": "gene_name",
    "variant": "variant_id",
    "transcript": "transcript_name",
    "protein": "protein_name",
    "experiment": "experiment_name",
    "dataset": "dataset_name",
    "study": "study_name",
    "project": "project_name",
}

SUPPORTED_DOMAINS: set[str] = set(DOMAIN_MAP.keys())


def _validate_domain(domain: str) -> None:
    if domain not in SUPPORTED_DOMAINS:
        domains_list = ", ".join(sorted(SUPPORTED_DOMAINS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported domain '{domain}'. Supported domains: {domains_list}",
        )


@router.get("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    query: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=10, ge=1, le=100),
    domain: str = Query(default="study"),
    field: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> SuggestionResponse:
    _validate_domain(domain)

    model = DOMAIN_MAP[domain]
    resolved_field = field if field is not None else DEFAULT_FIELDS[domain]

    if not hasattr(model, resolved_field):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field '{resolved_field}' does not exist on domain '{domain}'",
        )

    service = SearchService(session)
    cache = NullCache()
    return await service.suggest(
        model=model,
        column_name=resolved_field,
        query=query,
        limit=limit,
        domain=domain,
        cache=cache,
    )
