"""Minimal REST API for workflows.

Phase 7.1: definitions, run initialization, inspection.
Phase 7.2: synchronous in-process run execution (tests/internal use).
Phase 7.4: queueing a pending run for background worker execution.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from genomeai_api.dependencies import get_db_session
from genomeai_api.repositories.workflow import WorkflowRepository
from genomeai_api.schemas.workflow import (
    JobResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunQueueResponse,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from genomeai_api.services.workflow import QueueRunResult, WorkflowService
from genomeai_api.workflows.errors import QueueUnavailableError
from genomeai_api.workflows.execution.engine import DAGExecutionEngine
from genomeai_api.workflows.execution.executor import PassthroughStepExecutor
from genomeai_api.workflows.queueing import JobQueue

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _get_queue(request: Request) -> JobQueue | None:
    """Workflow queue for the current app state (None when unconfigured)."""
    state = getattr(request.app.state, "app_state", None)
    client = getattr(state, "redis", None) if state is not None else None
    if client is None:
        return None
    from genomeai_api.workflows.redis_queue import RedisJobQueue

    return RedisJobQueue(client)


async def _get_service(
    session: AsyncSession = Depends(get_db_session),
    queue: JobQueue | None = Depends(_get_queue),
) -> WorkflowService:
    return WorkflowService(WorkflowRepository(session), queue=queue)


async def _get_engine(session: AsyncSession = Depends(get_db_session)) -> DAGExecutionEngine:
    """Synchronous in-process engine (Phase 7.2).

    The default executor is deterministic passthrough; real executors plug
    in here once they exist.
    """
    return DAGExecutionEngine(
        repository=WorkflowRepository(session),
        executor=PassthroughStepExecutor(),
    )


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    return await service.create_workflow(data)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    service: WorkflowService = Depends(_get_service),
) -> list[WorkflowResponse]:
    return await service.list_workflows()


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    return await service.get_workflow(workflow_id)


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowResponse:
    result = await service.update_workflow(workflow_id, data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return result


@router.post(
    "/{workflow_id}/runs",
    response_model=WorkflowRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_run(
    workflow_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowRunResponse:
    return await service.create_run(workflow_id)


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_workflow_run(
    run_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowRunResponse:
    return await service.get_run(run_id)


@router.post("/runs/{run_id}/execute", response_model=WorkflowRunResponse)
async def execute_workflow_run(
    run_id: uuid.UUID,
    engine: DAGExecutionEngine = Depends(_get_engine),
) -> WorkflowRunResponse:
    """Executes one run synchronously, in-process.

    Phase 7.2 executes steps sequentially in topological order before
    responding; there is no background job or queue behind this endpoint.
    Kept for tests/internal use — clients should prefer queueing.
    """
    run = await engine.execute_run(run_id)
    return WorkflowRunResponse.model_validate(run)


@router.post(
    "/runs/{run_id}/queue",
    response_model=WorkflowRunQueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def queue_workflow_run(
    run_id: uuid.UUID,
    service: WorkflowService = Depends(_get_service),
) -> WorkflowRunQueueResponse:
    """Queues one pending run for background execution (Phase 7.4).

    The request does NOT execute the DAG and never blocks on it — a
    worker claims the job later and drives the same DAG engine. Repeated
    calls for an already-queued run are idempotent and return the
    original job identity.
    """
    try:
        result: QueueRunResult = await service.queue_run(run_id)
    except QueueUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return WorkflowRunQueueResponse(
        job=JobResponse(
            job_id=result.job_id,
            workflow_run_id=run_id,
            queued_at=result.queued_at,
        ),
        run=result.run,
    )
