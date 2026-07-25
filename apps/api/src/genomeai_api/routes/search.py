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
from genomeai_api.schemas.search import (
    CoordinateSearchRequest,
    CoordinateSearchResponse,
    DomainSearchRequest,
    FullTextSearchRequest,
    FullTextSearchResponse,
    SearchResponse,
    SuggestionResponse,
)
from genomeai_api.search.cache import NullCache
from genomeai_api.search.domain_search import DOMAIN_SEARCH_CONFIGS
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

SUPPORTED_DOMAINS: set[str] = set(DOMAIN_SEARCH_CONFIGS.keys())


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


@router.post("/{domain}", response_model=SearchResponse)
async def search_domain(
    domain: str,
    request: DomainSearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SearchResponse:
    _validate_domain(domain)
    config = DOMAIN_SEARCH_CONFIGS[domain]
    service = SearchService(session)
    return await service.domain_search(config, request)


@router.post("/{domain}/fts", response_model=FullTextSearchResponse)
async def search_domain_fts(
    domain: str,
    request: FullTextSearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> FullTextSearchResponse:
    _validate_domain(domain)
    config = DOMAIN_SEARCH_CONFIGS[domain]
    for col in request.fts.columns:
        if col not in config.fts_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Column '{col}' is not an FTS-searchable field for domain "
                    f"'{domain}'. Allowed: {', '.join(config.fts_fields)}"
                ),
            )
    domain_request = DomainSearchRequest(
        pagination=request.search.pagination,
        sort=request.search.sort,
        filters=request.search.filters,
        advanced_filters=request.search.advanced_filters,
    )
    service = SearchService(session)
    return await service.domain_search_fts(
        config,
        domain_request,
        fts_config=request.fts,
    )


@router.post("/{domain}/coordinate", response_model=CoordinateSearchResponse)
async def search_domain_coordinate(
    domain: str,
    request: CoordinateSearchRequest,
    session: AsyncSession = Depends(get_db_session),
) -> CoordinateSearchResponse:
    _validate_domain(domain)
    config = DOMAIN_SEARCH_CONFIGS[domain]
    if not config.has_coordinate_search:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Domain '{domain}' does not support coordinate search",
        )
    model = DOMAIN_MAP[domain]
    overrides: dict[str, str] = {}
    if request.chromosome_column == "chromosome":
        overrides["chromosome_column"] = config.coordinate_chromosome_column
    if request.start_column == "start_position":
        overrides["start_column"] = config.coordinate_start_column
    if request.end_column == "end_position":
        overrides["end_column"] = config.coordinate_end_column
    merged_request = CoordinateSearchRequest(
        interval=request.interval,
        match_type=request.match_type,
        pagination=request.pagination,
        sort=request.sort,
        filters=request.filters,
        advanced_filters=request.advanced_filters,
        chromosome_column=overrides.get("chromosome_column", request.chromosome_column),
        start_column=overrides.get("start_column", request.start_column),
        end_column=overrides.get("end_column", request.end_column),
    )
    service = SearchService(session)
    return await service.coordinate_search(model, merged_request)
