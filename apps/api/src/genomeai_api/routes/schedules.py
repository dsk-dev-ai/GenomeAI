"""Minimal REST API for workflow schedules (Phase 7.3).

Management of schedule definitions plus one explicit evaluation endpoint.
There is no daemon here: `/evaluate` performs a single deterministic
due-run detection pass when called, creating pending WorkflowRuns through
the existing mechanism. Execution remains the DAGExecutionEngine's job
(POST /workflows/runs/{run_id}/execute).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.schedule import ScheduleRepository
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse,
    SchedulerEvaluationResponse,
    ScheduleUpdate,
)
from genomeai_api.services.scheduler import SchedulerService

router = APIRouter(prefix="/workflows", tags=["workflows"])


async def _get_scheduler(
    session: AsyncSession = Depends(get_db_session),
) -> SchedulerService:
    return SchedulerService(
        schedules=ScheduleRepository(session),
        workflows=WorkflowRepository(session),
    )


@router.post(
    "/{workflow_id}/schedules",
    response_model=ScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    workflow_id: uuid.UUID,
    data: ScheduleCreate,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> ScheduleResponse:
    return await scheduler.create_schedule(workflow_id, data)


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    workflow_id: uuid.UUID | None = None,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> list[ScheduleResponse]:
    return await scheduler.list_schedules(workflow_id)


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: uuid.UUID,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> ScheduleResponse:
    return await scheduler.get_schedule(schedule_id)


@router.patch("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: uuid.UUID,
    data: ScheduleUpdate,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> ScheduleResponse:
    return await scheduler.update_schedule(schedule_id, data)


@router.post("/schedules/{schedule_id}/enable", response_model=ScheduleResponse)
async def enable_schedule(
    schedule_id: uuid.UUID,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> ScheduleResponse:
    return await scheduler.enable_schedule(schedule_id)


@router.post("/schedules/{schedule_id}/disable", response_model=ScheduleResponse)
async def disable_schedule(
    schedule_id: uuid.UUID,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> ScheduleResponse:
    return await scheduler.disable_schedule(schedule_id)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: uuid.UUID,
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> None:
    deleted = await scheduler.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )


@router.post("/schedules/evaluate", response_model=SchedulerEvaluationResponse)
async def evaluate_due_schedules(
    scheduler: SchedulerService = Depends(_get_scheduler),
) -> SchedulerEvaluationResponse:
    """One synchronous due-run detection pass.

    Application-level scheduling only: creates pending WorkflowRuns for
    every due enabled schedule. Nothing is enqueued and nothing executes.
    """
    result = await scheduler.evaluate_due()
    return SchedulerEvaluationResponse(
        evaluated_at=result.evaluated_at,
        created_runs=result.created_run_ids,
        skipped_duplicates=result.skipped_duplicates,
    )
