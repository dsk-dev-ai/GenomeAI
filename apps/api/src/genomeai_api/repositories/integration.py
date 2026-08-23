"""Repositories for the Data Integration Foundation tables."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.exceptions import (
    DuplicateDataSourceError,
    DuplicateExternalIdentifierError,
)
from genomeai_api.integration.identifiers import ExternalIdentifier
from genomeai_api.integration.jobs import IngestionJob
from genomeai_api.integration.models.data_source import DataSource
from genomeai_api.integration.models.external_identifier import (
    ExternalIdentifier as ExternalIdentifierRow,
)
from genomeai_api.integration.models.ingestion_job import IngestionJob as IngestionJobRow
from genomeai_api.integration.models.provenance import Provenance
from genomeai_api.integration.raw_data import ProvenanceRecord
from genomeai_api.integration.types import SyncStatus
from genomeai_api.schemas.integration import DataSourceCreate, DataSourceUpdate


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) == "23505"


class DataSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: DataSourceCreate) -> DataSource:
        row = DataSource(**data.model_dump())
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_unique_violation(exc):
                raise DuplicateDataSourceError from None
            raise
        await self._session.refresh(row)
        return row

    async def get_by_source_id(self, source_id: str) -> DataSource | None:
        result = await self._session.execute(
            select(DataSource).where(DataSource.source_id == source_id)
        )
        return result.scalars().first()

    async def list(self) -> list[DataSource]:
        result = await self._session.execute(
            select(DataSource).order_by(DataSource.source_id)
        )
        return list(result.scalars().all())

    async def update(self, source_id: str, data: DataSourceUpdate) -> DataSource | None:
        row = await self.get_by_source_id(source_id)
        if row is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def set_sync_state(
        self,
        source_id: str,
        *,
        sync_status: SyncStatus,
        source_version: str | None = None,
        last_synced_at: datetime | None = None,
    ) -> DataSource | None:
        row = await self.get_by_source_id(source_id)
        if row is None:
            return None
        row.sync_status = sync_status.value
        if source_version is not None:
            row.source_version = source_version
        if last_synced_at is not None:
            row.last_synced_at = last_synced_at
        await self._session.commit()
        await self._session.refresh(row)
        return row


class ExternalIdentifierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, identifier: ExternalIdentifier) -> ExternalIdentifierRow:
        row = ExternalIdentifierRow(
            source_id=identifier.source,
            external_id=identifier.external_id,
            entity_type=identifier.entity_type,
            genomeai_entity_id=identifier.genomeai_entity_id,
            namespace=identifier.namespace,
            version=identifier.version,
        )
        self._session.add(row)
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            if _is_unique_violation(exc):
                raise DuplicateExternalIdentifierError from None
            raise
        await self._session.refresh(row)
        return row

    async def get(
        self,
        *,
        source_id: str,
        external_id: str,
        entity_type: str,
        namespace: str | None = None,
    ) -> ExternalIdentifierRow | None:
        stmt = select(ExternalIdentifierRow).where(
            ExternalIdentifierRow.source_id == source_id,
            ExternalIdentifierRow.external_id == external_id,
            ExternalIdentifierRow.entity_type == entity_type,
        )
        if namespace is None:
            stmt = stmt.where(ExternalIdentifierRow.namespace.is_(None))
        else:
            stmt = stmt.where(ExternalIdentifierRow.namespace == namespace)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_for_entity(
        self, *, entity_type: str, genomeai_entity_id: uuid.UUID
    ) -> list[ExternalIdentifierRow]:
        result = await self._session.execute(
            select(ExternalIdentifierRow)
            .where(
                ExternalIdentifierRow.entity_type == entity_type,
                ExternalIdentifierRow.genomeai_entity_id == genomeai_entity_id,
            )
            .order_by(ExternalIdentifierRow.created_at)
        )
        return list(result.scalars().all())

    async def list_by_source(self, *, source_id: str) -> list[ExternalIdentifierRow]:
        result = await self._session.execute(
            select(ExternalIdentifierRow)
            .where(ExternalIdentifierRow.source_id == source_id)
            .order_by(ExternalIdentifierRow.created_at)
        )
        return list(result.scalars().all())


class ProvenanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: ProvenanceRecord) -> Provenance:
        row = Provenance(
            source_id=record.source,
            source_record_id=record.source_record_id,
            source_version=record.source_release,
            retrieved_at=datetime.fromisoformat(record.retrieved_at),
            checksum=record.checksum,
            source_url=record.source_url,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row


class IngestionJobRepository:
    """Persists the domain :class:`IngestionJob` state machine.

    Transition rules live in the domain object; this repository only maps it
    to/from the ``ingestion_jobs`` row.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: IngestionJob) -> IngestionJob:
        row = IngestionJobRow(
            id=uuid.UUID(job.job_id),
            source_id=job.source_id,
            state=job.state.value,
            started_at=job.started_at,
            finished_at=job.finished_at,
            records_received=job.records_received,
            records_succeeded=job.records_succeeded,
            records_failed=job.records_failed,
            error_message=job.error_message,
            error_detail=job.error_detail,
        )
        self._session.add(row)
        await self._session.commit()
        return job

    async def save(self, job: IngestionJob) -> IngestionJob:
        row = await self._session.get(IngestionJobRow, uuid.UUID(job.job_id))
        if row is None:
            raise LookupError(f"Ingestion job '{job.job_id}' does not exist")
        row.state = job.state.value
        row.started_at = job.started_at
        row.finished_at = job.finished_at
        row.records_received = job.records_received
        row.records_succeeded = job.records_succeeded
        row.records_failed = job.records_failed
        row.error_message = job.error_message
        row.error_detail = job.error_detail
        await self._session.commit()
        return job

    async def get(self, job_id: str) -> IngestionJob | None:
        try:
            key = uuid.UUID(job_id)
        except ValueError:
            return None
        row = await self._session.get(IngestionJobRow, key)
        if row is None:
            return None
        return _row_to_domain(row)

    async def list_by_source(self, source_id: str) -> list[IngestionJob]:
        result = await self._session.execute(
            select(IngestionJobRow)
            .where(IngestionJobRow.source_id == source_id)
            .order_by(IngestionJobRow.created_at.desc())
        )
        return [_row_to_domain(row) for row in result.scalars().all()]


def _row_to_domain(row: IngestionJobRow) -> IngestionJob:
    from genomeai_api.integration.types import JobState

    return IngestionJob(
        source_id=row.source_id,
        job_id=str(row.id),
        state=JobState(row.state),
        started_at=row.started_at,
        finished_at=row.finished_at,
        records_received=row.records_received,
        records_succeeded=row.records_succeeded,
        records_failed=row.records_failed,
        error_message=row.error_message,
        error_detail=row.error_detail,
    )
