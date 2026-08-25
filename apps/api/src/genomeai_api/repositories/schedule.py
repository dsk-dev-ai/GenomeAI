"""Repository for workflow schedules (Phase 7.3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.schemas.schedule import ScheduleUpdate
from genomeai_api.workflows.models.workflow_schedule import WorkflowSchedule


class ScheduleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, schedule: WorkflowSchedule) -> WorkflowSchedule:
        self._session.add(schedule)
        await self._session.commit()
        return await self.get_by_id(schedule.id) or schedule

    async def get_by_id(self, schedule_id: uuid.UUID) -> WorkflowSchedule | None:
        result = await self._session.execute(
            select(WorkflowSchedule).where(WorkflowSchedule.id == schedule_id)
        )
        return result.scalars().first()

    async def list(self, workflow_id: uuid.UUID | None = None) -> list[WorkflowSchedule]:
        stmt = select(WorkflowSchedule).order_by(WorkflowSchedule.created_at.desc())
        if workflow_id is not None:
            stmt = stmt.where(WorkflowSchedule.workflow_id == workflow_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_enabled(self) -> list[WorkflowSchedule]:
        """Enabled schedules only — the due-detection scan set."""
        result = await self._session.execute(
            select(WorkflowSchedule).where(WorkflowSchedule.state == "enabled")
        )
        return list(result.scalars().all())

    async def update_fields(
        self,
        schedule_id: uuid.UUID,
        data: ScheduleUpdate,
    ) -> WorkflowSchedule | None:
        """Applies partial spec updates; lifecycle state is not settable here."""
        schedule = await self._session.get(WorkflowSchedule, schedule_id)
        if schedule is None:
            return None
        fields = data.model_dump(exclude_unset=True)
        for key, value in fields.items():
            setattr(schedule, key, value)
        await self._session.commit()
        return await self.get_by_id(schedule_id)

    async def reschedule(
        self,
        schedule_id: uuid.UUID,
        *,
        next_run_at: datetime | None,
    ) -> None:
        """Recomputes only the next occurrence (spec changes, re-enabling).

        Never touches `last_run_at` or lifecycle state.
        """
        schedule = await self._session.get(WorkflowSchedule, schedule_id)
        if schedule is None:
            return
        schedule.next_run_at = next_run_at
        await self._session.commit()

    async def set_state(self, schedule_id: uuid.UUID, state: str) -> None:
        """Persists a lifecycle-state change decided by the service."""
        schedule = await self._session.get(WorkflowSchedule, schedule_id)
        if schedule is None:
            return
        schedule.state = state
        await self._session.commit()

    async def record_occurrence(
        self,
        schedule_id: uuid.UUID,
        *,
        last_run_at: datetime,
        next_run_at: datetime | None,
        state: str,
    ) -> None:
        """Records that one occurrence was handled.

        `next_run_at=None` + completed state is the one-time terminal form;
        recurring schedules receive their next computed occurrence.
        """
        schedule = await self._session.get(WorkflowSchedule, schedule_id)
        if schedule is None:
            return
        schedule.last_run_at = last_run_at
        schedule.next_run_at = next_run_at
        schedule.state = state
        await self._session.commit()

    async def delete(self, schedule_id: uuid.UUID) -> bool:
        schedule = await self._session.get(WorkflowSchedule, schedule_id)
        if schedule is None:
            return False
        await self._session.delete(schedule)
        await self._session.commit()
        return True
