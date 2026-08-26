from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.step_run import StepRun
    from genomeai_api.workflows.models.workflow import Workflow
    from genomeai_api.workflows.models.workflow_schedule import WorkflowSchedule


class WorkflowRun(Base):
    """One requested execution of a workflow.

    Phase 7.1 creates runs in the PENDING state and initializes their step
    runs. Phase 7.3 annotates scheduler-created runs with their schedule
    and occurrence; the partial unique index makes duplicate creation of
    one occurrence impossible at the database level.
    """

    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index("ix_workflow_runs_workflow_state", "workflow_id", "state"),
        Index(
            "uq_workflow_runs_schedule_occurrence",
            "schedule_id",
            "scheduled_for",
            unique=True,
            postgresql_where=text(
                "schedule_id IS NOT NULL AND scheduled_for IS NOT NULL"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Phase 7.5 retry tracking. attempt_count increments every time the
    # engine starts this run (one execution attempt); failure metadata is
    # appended by the repository's record_run_failure, never overwritten.
    attempt_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0, server_default=text("0")
    )
    failure_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_history: Mapped[list[dict[str, object]] | None] = mapped_column(
        JSONB(), nullable=True
    )

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="runs")
    schedule: Mapped[WorkflowSchedule | None] = relationship(
        "WorkflowSchedule",
        back_populates="runs",
    )
    step_runs: Mapped[list[StepRun]] = relationship(
        "StepRun",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="StepRun.position",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
