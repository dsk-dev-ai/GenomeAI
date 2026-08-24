from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genomeai_api.database.base import Base

if TYPE_CHECKING:
    from genomeai_api.workflows.models.workflow_dependency import WorkflowDependency
    from genomeai_api.workflows.models.workflow_run import WorkflowRun
    from genomeai_api.workflows.models.workflow_step import WorkflowStep


class Workflow(Base):
    """A reusable workflow definition (DAG of typed steps).

    Phase 7.1 stores and validates definitions; nothing executes them yet.
    """

    __tablename__ = "workflows"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="ck_workflow_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="0.1.0", default="0.1.0"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="draft", default="draft"
    )

    steps: Mapped[list[WorkflowStep]] = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.position",
    )
    dependencies: Mapped[list[WorkflowDependency]] = relationship(
        "WorkflowDependency",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    runs: Mapped[list[WorkflowRun]] = relationship(
        "WorkflowRun",
        back_populates="workflow",
        cascade="all, delete-orphan",
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
