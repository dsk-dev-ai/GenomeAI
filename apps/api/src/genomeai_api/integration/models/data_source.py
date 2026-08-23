from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from genomeai_api.database.base import Base


class DataSource(Base):
    """Registry row describing ONE external scientific data source."""

    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    api_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    documentation_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    auth_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    # Name of the env/config reference that holds the secret — never the secret.
    credential_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rate_limit: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    license_info: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
    )
    access_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="live")
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    feature_flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default="{}", default=dict
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
