"""Repository for the Workflow Foundation tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from genomeai_api.schemas.workflow import WorkflowCreate, WorkflowUpdate
from genomeai_api.workflows.models.step_run import StepRun
from genomeai_api.workflows.models.workflow import Workflow
from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency
from genomeai_api.workflows.models.workflow_run import WorkflowRun
from genomeai_api.workflows.models.workflow_step import WorkflowStep


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: WorkflowCreate) -> Workflow:
        """Persists a workflow with steps and name-resolved dependencies.

        Callers must DAG-validate the payload first; step ids are generated
        eagerly so dependency edges can reference them before the flush.
        """
        workflow = Workflow(
            name=data.name,
            description=data.description,
            version=data.version,
        )
        step_rows: dict[str, WorkflowStep] = {}
        for spec in data.steps:
            row = WorkflowStep(
                id=uuid.uuid4(),
                name=spec.name,
                step_type=spec.step_type,
                configuration=spec.configuration,
                position=spec.position,
            )
            step_rows[spec.name] = row
            workflow.steps.append(row)

        for dep in data.dependencies:
            workflow.dependencies.append(
                WorkflowDependency(
                    from_step_id=step_rows[dep.from_step].id,
                    to_step_id=step_rows[dep.to_step].id,
                )
            )

        self._session.add(workflow)
        await self._session.commit()
        created = await self.get_by_id(workflow.id)
        assert created is not None  # same session; just persisted
        return created

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        stmt = (
            select(Workflow)
            .options(
                selectinload(Workflow.steps),
                selectinload(Workflow.dependencies),
            )
            .where(Workflow.id == workflow_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list(self) -> list[Workflow]:
        stmt = (
            select(Workflow)
            .options(
                selectinload(Workflow.steps),
                selectinload(Workflow.dependencies),
            )
            .order_by(Workflow.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_metadata(
        self, workflow_id: uuid.UUID, data: WorkflowUpdate
    ) -> Workflow | None:
        workflow = await self._session.get(Workflow, workflow_id)
        if workflow is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(workflow, key, value)
        await self._session.commit()
        return await self.get_by_id(workflow_id)

    async def create_run(
        self, workflow_id: uuid.UUID, ordered_step_ids: list[uuid.UUID]
    ) -> WorkflowRun:
        """Creates a pending run plus one pending StepRun per step.

        `ordered_step_ids` is the deterministic topological order computed by
        the service; persistence preserves it via insertion order.
        """
        run = WorkflowRun(workflow_id=workflow_id)
        for step_id in ordered_step_ids:
            run.step_runs.append(StepRun(step_id=step_id))
        self._session.add(run)
        await self._session.commit()
        created = await self.get_run(run.id)
        assert created is not None  # same session; just persisted
        return created

    async def get_run(self, run_id: uuid.UUID) -> WorkflowRun | None:
        stmt = (
            select(WorkflowRun)
            .options(selectinload(WorkflowRun.step_runs))
            .where(WorkflowRun.id == run_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()
