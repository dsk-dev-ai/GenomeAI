from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.workflow import Workflow
    from genomeai_api.workflows.models.workflow_run import WorkflowRun


class WorkflowSchedule(Base):
    """Determines WHEN a workflow run should start (Phase 7.3).

    One schedule belongs to exactly one workflow. Recurring schedules carry
    a cron `expression` interpreted in `timezone`; one-time schedules carry
    an absolute `run_at` (UTC). The scheduler advances `next_run_at`,
    stamps `last_run_at`, and completes one-time schedules — it never
    executes anything itself.
    """

    __tablename__ = "workflow_schedules"
    __table_args__ = (
        CheckConstraint(
            "schedule_type IN ('once', 'recurring')",
            name="ck_schedule_type",
        ),
        CheckConstraint(
            "state IN ('enabled', 'disabled', 'completed')",
            name="ck_schedule_state",
        ),
        CheckConstraint(
            "("
            "(schedule_type = 'once' AND run_at IS NOT NULL AND expression IS NULL)"
            " OR "
            "(schedule_type = 'recurring' AND expression IS NOT NULL AND run_at IS NULL)"
            ")",
            name="ck_schedule_shape_matches_type",
        ),
        Index("ix_workflow_schedules_state_next_run", "state", "next_run_at"),
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
    schedule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    expression: Mapped[str | None] = mapped_column(String(255), nullable=True)
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone_name: Mapped[str] = mapped_column(
        String(64), nullable=False, server_default="UTC", default="UTC"
    )
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="enabled", default="enabled"
    )
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="schedules")
    runs: Mapped[list[WorkflowRun]] = relationship(
        "WorkflowRun",
        back_populates="schedule",
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
