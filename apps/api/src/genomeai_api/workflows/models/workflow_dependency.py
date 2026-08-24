from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.workflow import Workflow
    from genomeai_api.workflows.models.workflow_step import WorkflowStep


class WorkflowDependency(Base):
    """A directed edge between two steps of the SAME workflow: from → to.

    Both endpoints are enforced by composite foreign keys
    ``(workflow_id, from_step_id)`` / ``(workflow_id, to_step_id)`` into
    ``workflow_steps(workflow_id, id)``, so a dependency can never connect
    steps that belong to different workflows — even via raw SQL.
    """

    __tablename__ = "workflow_dependencies"
    __table_args__ = (
        UniqueConstraint("from_step_id", "to_step_id", name="uq_workflow_dependency_edge"),
        CheckConstraint("from_step_id <> to_step_id", name="ck_workflow_dependency_not_self"),
        ForeignKeyConstraint(
            ["workflow_id", "from_step_id"],
            ["workflow_steps.workflow_id", "workflow_steps.id"],
            name="fk_workflow_dependency_from_step",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["workflow_id", "to_step_id"],
            ["workflow_steps.workflow_id", "workflow_steps.id"],
            name="fk_workflow_dependency_to_step",
            ondelete="CASCADE",
        ),
        Index("ix_workflow_dependencies_from_step_id", "from_step_id"),
        Index("ix_workflow_dependencies_to_step_id", "to_step_id"),
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
    from_step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_step_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    workflow: Mapped[Workflow] = relationship("Workflow", back_populates="dependencies")
    from_step: Mapped[WorkflowStep] = relationship(
        "WorkflowStep", back_populates="as_source_dependencies", foreign_keys=[from_step_id]
    )
    to_step: Mapped[WorkflowStep] = relationship(
        "WorkflowStep", back_populates="as_target_dependencies", foreign_keys=[to_step_id]
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
