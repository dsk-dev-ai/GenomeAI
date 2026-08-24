from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.step_run import StepRun
    from genomeai_api.workflows.models.workflow import Workflow
    from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency


class WorkflowStep(Base):
    """One executable logical step inside a workflow (not executed yet)."""

    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("workflow_id", "name", name="uq_workflow_step_name"),
        Index("ix_workflow_steps_workflow_position", "workflow_id", "position"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    step_type: Mapped[str] = mapped_column(String(100), nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="steps")
    as_source_dependencies: Mapped[list[WorkflowDependency]] = relationship(
        "WorkflowDependency",
        back_populates="from_step",
        foreign_keys="WorkflowDependency.from_step_id",
        cascade="all, delete-orphan",
    )
    as_target_dependencies: Mapped[list[WorkflowDependency]] = relationship(
        "WorkflowDependency",
        back_populates="to_step",
        foreign_keys="WorkflowDependency.to_step_id",
        cascade="all, delete-orphan",
    )
    step_runs: Mapped[list[StepRun]] = relationship(
        "StepRun", back_populates="step", cascade="all, delete-orphan"
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
