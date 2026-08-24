from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.workflow_run import WorkflowRun
    from genomeai_api.workflows.models.workflow_step import WorkflowStep


class StepRun(Base):
    """Execution state of one workflow step within one workflow run.

    Created deterministically when a run is requested (one per step, in
    topological order). The execution engine advances these states and
    records each step's output or failure reason here.
    """

    __tablename__ = "workflow_step_runs"
    __table_args__ = (
        UniqueConstraint("run_id", "step_id", name="uq_workflow_step_run"),
        Index("ix_workflow_step_runs_run_state", "run_id", "state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    # Persisted topological ordinal within the run; created_at ties are common
    # for same-transaction inserts, so ordering must not rely on timestamps.
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[WorkflowRun] = relationship("WorkflowRun", back_populates="step_runs")
    step: Mapped[WorkflowStep] = relationship(
        "WorkflowStep", back_populates="step_runs"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
