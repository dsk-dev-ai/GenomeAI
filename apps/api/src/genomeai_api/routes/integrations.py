"""Minimal internal/admin API for the Data Integration Foundation.

These endpoints expose the integration foundation itself (registry, sources,
connector health, identifiers, ingestion-job state). They never proxy raw
third-party APIs and never accept user-supplied fetch targets.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from genomeai_config import Settings
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session, get_settings
from genomeai_api.integration.registry import SourceRegistry
from genomeai_api.integration.services_bootstrap import build_default_registry
from genomeai_api.repositories.integration import (
    DataSourceRepository,
    ExternalIdentifierRepository,
    IngestionJobRepository,
    ProvenanceRepository,
)
from genomeai_api.schemas.integration import (
    ConnectorHealthResponse,
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    ExternalIdentifierCreate,
    ExternalIdentifierResponse,
    IngestionJobComplete,
    IngestionJobCreate,
    IngestionJobFailure,
    IngestionJobResponse,
)
from genomeai_api.services.integration import IntegrationService

router = APIRouter(prefix="/integration", tags=["integration"])


def _get_registry() -> SourceRegistry:
    return build_default_registry()


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    registry: SourceRegistry = Depends(_get_registry),
) -> IntegrationService:
    integration = settings.integration
    return IntegrationService(
        sources=DataSourceRepository(session),
        identifiers=ExternalIdentifierRepository(session),
        provenance=ProvenanceRepository(session),
        jobs=IngestionJobRepository(session),
        registry=registry,
        allowed_source_urls=list(integration.allowed_source_urls),
        request_timeout_seconds=integration.request_timeout_seconds,
        default_max_retries=integration.default_max_retries,
    )


@router.get("/connectors")
async def list_connectors(
    service: IntegrationService = Depends(_get_service),
) -> list[dict[str, object]]:
    """Static metadata for connectors compiled into the service."""
    return service.registered_connectors()


@router.get("/sources", response_model=list[DataSourceResponse])
async def list_sources(
    service: IntegrationService = Depends(_get_service),
) -> list[DataSourceResponse]:
    return await service.list_sources()


@router.post("/sources", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
async def register_source(
    data: DataSourceCreate,
    service: IntegrationService = Depends(_get_service),
) -> DataSourceResponse:
    return await service.register_source(data)


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_source(
    source_id: str,
    service: IntegrationService = Depends(_get_service),
) -> DataSourceResponse:
    return await service.get_source(source_id)


@router.patch("/sources/{source_id}", response_model=DataSourceResponse)
async def update_source(
    source_id: str,
    data: DataSourceUpdate,
    service: IntegrationService = Depends(_get_service),
) -> DataSourceResponse:
    result = await service.update_source(source_id, data)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Data source not found")
    return result


@router.get("/sources/{source_id}/health", response_model=ConnectorHealthResponse)
async def check_source_health(
    source_id: str,
    service: IntegrationService = Depends(_get_service),
) -> ConnectorHealthResponse:
    return await service.check_source_health(source_id)


@router.post(
    "/identifiers",
    response_model=ExternalIdentifierResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_identifier(
    data: ExternalIdentifierCreate,
    service: IntegrationService = Depends(_get_service),
) -> ExternalIdentifierResponse:
    return await service.create_identifier(data)


@router.get("/identifiers", response_model=ExternalIdentifierResponse | None)
async def lookup_identifier(
    source_id: str = Query(max_length=100),
    external_id: str = Query(min_length=1, max_length=255),
    entity_type: str = Query(min_length=1, max_length=50),
    namespace: str | None = Query(default=None, max_length=100),
    service: IntegrationService = Depends(_get_service),
) -> ExternalIdentifierResponse | None:
    return await service.get_identifier(
        source_id=source_id,
        external_id=external_id,
        entity_type=entity_type,
        namespace=namespace,
    )


@router.get(
    "/entities/{entity_type}/{genomeai_entity_id}/identifiers",
    response_model=list[ExternalIdentifierResponse],
)
async def list_entity_identifiers(
    entity_type: str,
    genomeai_entity_id: uuid.UUID,
    service: IntegrationService = Depends(_get_service),
) -> list[ExternalIdentifierResponse]:
    return await service.list_identifiers_for_entity(entity_type, genomeai_entity_id)


@router.post("/jobs", response_model=IngestionJobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: IngestionJobCreate,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    return await service.create_job(payload.source_id)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_job(
    job_id: str,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    result = await service.get_job(job_id)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ingestion job not found")
    return result


@router.post("/jobs/{job_id}/start", response_model=IngestionJobResponse)
async def start_job(
    job_id: str,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    return await service.start_job(job_id)


@router.post("/jobs/{job_id}/complete", response_model=IngestionJobResponse)
async def complete_job(
    job_id: str,
    payload: IngestionJobComplete,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    return await service.complete_job(
        job_id, received=payload.received, succeeded=payload.succeeded
    )


@router.post("/jobs/{job_id}/fail", response_model=IngestionJobResponse)
async def fail_job(
    job_id: str,
    payload: IngestionJobFailure,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    return await service.fail_job(
        job_id,
        received=payload.received,
        failed=payload.failed,
        error_message=payload.error_message,
    )


@router.post("/jobs/{job_id}/cancel", response_model=IngestionJobResponse)
async def cancel_job(
    job_id: str,
    service: IntegrationService = Depends(_get_service),
) -> IngestionJobResponse:
    return await service.cancel_job(job_id)
