"""Service layer for the Data Integration Foundation admin surfaces.

Orchestrates the source registry, the connector factories, and the persistence
repositories. All outbound fetches run through the allowlisted ``HttpFetcher``;
no route ever receives a user-supplied fetch target.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from genomeai_api.integration.connectors.base import (
    ConnectorHealth,
    DataSourceConfig,
    DataSourceConnector,
)
from genomeai_api.integration.connectors.fetcher import HttpFetcher
from genomeai_api.integration.errors import (
    ConnectorNotFoundError,
    DataSourceNotFoundError,
    IntegrationConfigurationError,
)
from genomeai_api.integration.identifiers import ExternalIdentifier
from genomeai_api.integration.jobs import IngestionJob
from genomeai_api.integration.models.data_source import DataSource
from genomeai_api.integration.raw_data import ProvenanceRecord
from genomeai_api.integration.registry import SourceRegistry
from genomeai_api.integration.types import JobState, SyncStatus
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
    IngestionJobResponse,
)

_JOB_TERMINAL_STATES: frozenset[JobState] = frozenset(
    {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}
)


class IntegrationService:
    """Admin-facing operations over the integration foundation."""

    def __init__(
        self,
        sources: DataSourceRepository,
        identifiers: ExternalIdentifierRepository,
        provenance: ProvenanceRepository,
        jobs: IngestionJobRepository,
        registry: SourceRegistry,
        *,
        allowed_source_urls: list[str],
        request_timeout_seconds: float = 30.0,
        default_max_retries: int = 0,
    ) -> None:
        self._sources = sources
        self._identifiers = identifiers
        self._provenance = provenance
        self._jobs = jobs
        self._registry = registry
        self._allowed_source_urls = allowed_source_urls
        self._request_timeout_seconds = request_timeout_seconds
        self._default_max_retries = default_max_retries

    # ------------------------------------------------------------------ sources

    def registered_connectors(self) -> list[dict[str, object]]:
        return [
            {
                "source_id": d.source_id,
                "provider": d.provider,
                "display_name": d.display_name,
                "source_type": d.source_type.value,
                "access_mode": d.access_mode.value,
                "auth_mode": d.authentication_mode.value,
                "documentation_url": d.documentation_url,
                "description": d.description,
            }
            for d in self._registry.list_definitions()
        ]

    async def register_source(self, data: DataSourceCreate) -> DataSourceResponse:
        from genomeai_api.integration.connectors.fetcher import validate_allowed_url

        if not self._registry.has(data.source_id):
            raise ConnectorNotFoundError(data.source_id)
        validate_allowed_url(data.api_base_url, self._allowed_source_urls)
        row = await self._sources.create(data)
        return DataSourceResponse.model_validate(row)

    async def list_sources(self) -> list[DataSourceResponse]:
        rows = await self._sources.list()
        return [DataSourceResponse.model_validate(r) for r in rows]

    async def get_source(self, source_id: str) -> DataSourceResponse:
        row = await self._require_source(source_id)
        return DataSourceResponse.model_validate(row)

    async def update_source(
        self, source_id: str, data: DataSourceUpdate
    ) -> DataSourceResponse | None:
        row = await self._sources.update(source_id, data)
        if row is None:
            return None
        return DataSourceResponse.model_validate(row)

    # ------------------------------------------------------------------- health

    async def check_source_health(self, source_id: str) -> ConnectorHealthResponse:
        row = await self._require_source(source_id)
        if not row.enabled:
            raise IntegrationConfigurationError(
                f"Data source '{source_id}' is disabled"
            )
        config = DataSourceConfig(
            source_id=source_id,
            api_base_url=row.api_base_url,
            request_timeout_seconds=self._request_timeout_seconds,
            max_retries=self._default_max_retries,
            credential_ref=row.credential_ref,
            enabled=True,
            feature_flags=row.feature_flags,
        )
        fetcher = self._build_fetcher(config)
        try:
            connector: DataSourceConnector = self._registry.build_connector(
                source_id, config, fetcher=fetcher
            )
            health = await self._health_with_latency(connector)
        finally:
            await fetcher.aclose()

        version = connector.current_version
        await self._sources.set_sync_state(
            source_id,
            sync_status=SyncStatus.IDLE if health.ok else SyncStatus.FAILED,
            source_version=version,
        )
        return ConnectorHealthResponse(
            source_id=health.source_id,
            ok=health.ok,
            checked_at=health.checked_at,
            message=health.message,
            latency_ms=health.latency_ms,
        )

    async def _health_with_latency(
        self, connector: DataSourceConnector
    ) -> ConnectorHealth:
        started = datetime.now(UTC).timestamp()
        health = await connector.health_check()
        latency_ms = int((datetime.now(UTC).timestamp() - started) * 1000)
        return ConnectorHealth(
            source_id=health.source_id,
            ok=health.ok,
            checked_at=health.checked_at,
            message=health.message,
            latency_ms=latency_ms,
        )

    def _build_fetcher(self, config: DataSourceConfig) -> HttpFetcher:
        return HttpFetcher(
            config.api_base_url,
            allowed_source_urls=self._allowed_source_urls,
            request_timeout_seconds=self._request_timeout_seconds,
            default_max_retries=self._default_max_retries,
        )

    async def _require_source(self, source_id: str) -> DataSource:
        row = await self._sources.get_by_source_id(source_id)
        if row is None:
            raise DataSourceNotFoundError(source_id)
        return row

    # ---------------------------------------------------- external identifiers

    async def create_identifier(
        self, data: ExternalIdentifierCreate
    ) -> ExternalIdentifierResponse:
        await self._require_source(data.source_id)
        identifier = ExternalIdentifier(
            source=data.source_id,
            external_id=data.external_id,
            entity_type=data.entity_type.value,
            genomeai_entity_id=data.genomeai_entity_id,
            namespace=data.namespace,
            version=data.version,
        )
        row = await self._identifiers.create(identifier)
        return ExternalIdentifierResponse.model_validate(row)

    async def get_identifier(
        self,
        *,
        source_id: str,
        external_id: str,
        entity_type: str,
        namespace: str | None = None,
    ) -> ExternalIdentifierResponse | None:
        row = await self._identifiers.get(
            source_id=source_id,
            external_id=external_id,
            entity_type=entity_type,
            namespace=namespace,
        )
        if row is None:
            return None
        return ExternalIdentifierResponse.model_validate(row)

    async def list_identifiers_for_entity(
        self, entity_type: str, genomeai_entity_id: uuid.UUID
    ) -> list[ExternalIdentifierResponse]:
        rows = await self._identifiers.list_for_entity(
            entity_type=entity_type, genomeai_entity_id=genomeai_entity_id
        )
        return [ExternalIdentifierResponse.model_validate(r) for r in rows]

    async def list_identifiers_for_source(
        self, source_id: str
    ) -> list[ExternalIdentifierResponse]:
        await self._require_source(source_id)
        rows = await self._identifiers.list_by_source(source_id=source_id)
        return [ExternalIdentifierResponse.model_validate(r) for r in rows]

    # ----------------------------------------------------------------- jobs

    async def create_job(self, source_id: str) -> IngestionJobResponse:
        await self._require_source(source_id)
        job = IngestionJob(source_id=source_id)
        await self._jobs.create(job)
        return _job_response(job)

    async def start_job(self, job_id: str) -> IngestionJobResponse:
        job = await self._get_job(job_id)
        job.start()
        await self._jobs.save(job)
        await self._mark_sync(job.source_id, SyncStatus.RUNNING)
        return _job_response(job)

    async def complete_job(
        self, job_id: str, *, received: int, succeeded: int
    ) -> IngestionJobResponse:
        job = await self._get_job(job_id)
        job.succeed(received=received, succeeded=succeeded)
        await self._jobs.save(job)
        status = SyncStatus.SUCCEEDED if job.records_failed == 0 else SyncStatus.FAILED
        await self._mark_sync(job.source_id, status, set_last_synced=True)
        return _job_response(job)

    async def fail_job(
        self,
        job_id: str,
        *,
        received: int,
        failed: int,
        error_message: str,
        error_detail: dict[str, object] | None = None,
    ) -> IngestionJobResponse:
        job = await self._get_job(job_id)
        job.fail(
            received=received,
            failed=failed,
            error_message=error_message,
            error_detail=error_detail,
        )
        await self._jobs.save(job)
        await self._mark_sync(job.source_id, SyncStatus.FAILED, set_last_synced=True)
        return _job_response(job)

    async def cancel_job(self, job_id: str) -> IngestionJobResponse:
        job = await self._get_job(job_id)
        job.cancel()
        await self._jobs.save(job)
        await self._mark_sync(job.source_id, SyncStatus.IDLE)
        return _job_response(job)

    async def get_job(self, job_id: str) -> IngestionJobResponse | None:
        job = await self._jobs.get(job_id)
        if job is None:
            return None
        return _job_response(job)

    async def list_jobs(self, source_id: str) -> list[IngestionJobResponse]:
        jobs = await self._jobs.list_by_source(source_id)
        return [_job_response(j) for j in jobs]

    async def record_provenance(self, record: ProvenanceRecord):
        """Persists one provenance row for an ingested external record."""
        return await self._provenance.create(record)

    async def _get_job(self, job_id: str) -> IngestionJob:
        job = await self._jobs.get(job_id)
        if job is None:
            raise ValueError(f"Ingestion job '{job_id}' does not exist")
        return job

    async def _mark_sync(
        self,
        source_id: str,
        sync_status: SyncStatus,
        *,
        set_last_synced: bool = False,
    ) -> None:
        await self._sources.set_sync_state(
            source_id,
            sync_status=sync_status,
            last_synced_at=datetime.now(UTC) if set_last_synced else None,
        )


def _job_response(job: IngestionJob) -> IngestionJobResponse:
    return IngestionJobResponse(
        id=uuid.UUID(job.job_id),
        source_id=job.source_id,
        state=job.state,
        started_at=job.started_at,
        finished_at=job.finished_at,
        records_received=job.records_received,
        records_succeeded=job.records_succeeded,
        records_failed=job.records_failed,
        error_message=job.error_message,
        created_at=job.started_at or datetime.now(UTC),
    )


__all__ = ["IntegrationService"]
