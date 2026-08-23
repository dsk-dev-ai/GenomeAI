"""Connector interface for the Data Integration Foundation.

A connector wraps ONE external scientific source behind a strongly typed,
provider-agnostic interface. Provider-specific behavior (URLs, payload shapes,
rate-limit quirks) belongs inside individual connector implementations — never
in this module or in the core fetcher.

Runtime boundary: a connector is always bound to a `DataSourceConfig` built
from a persisted data-source record plus the integration settings. It never
accepts arbitrary user-supplied URLs (see the fetcher allowlist).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime

from genomeai_api.integration.types import AccessMode, AuthMode, SourceType


@dataclass(frozen=True)
class DataSourceDefinition:
    """Static metadata a connector declares about its source.

    License/access data is carried as connector-supplied configuration data —
    GenomeAI never asserts legal terms itself.
    """

    source_id: str
    provider: str
    display_name: str
    source_type: SourceType
    documentation_url: str | None = None
    access_mode: AccessMode = AccessMode.LIVE
    authentication_mode: AuthMode = AuthMode.NONE
    license_info: dict[str, str | None] = field(default_factory=dict)
    description: str | None = None


@dataclass(frozen=True)
class DataSourceConfig:
    """Runtime binding that gives a connector everything it needs to run.

    `credential_ref` names an environment/config reference (never a secret),
    and `feature_flags` come from the persisted source row.
    """

    source_id: str
    api_base_url: str
    request_timeout_seconds: float = 30.0
    max_retries: int = 0
    credential_ref: str | None = None
    enabled: bool = True
    feature_flags: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectorHealth:
    """Result of a connector health check."""

    source_id: str
    ok: bool
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    message: str = ""
    latency_ms: int | None = None


class DataSourceConnector(ABC):
    """Contract every source connector implements.

    Implementations stay thin: they translate a typed request into an HTTP
    call through an injected, allowlisted fetcher (owned by the subclass),
    build normalized records, and surface health.
    """

    definition: DataSourceDefinition

    def __init__(self, config: DataSourceConfig) -> None:
        self.config = config
        if not config.enabled:
            self._raise_disabled()

    def _raise_disabled(self) -> None:
        from genomeai_api.integration.errors import IntegrationConfigurationError

        raise IntegrationConfigurationError(
            f"Data source '{self.config.source_id}' is disabled"
        )

    @property
    @abstractmethod
    def current_version(self) -> str | None:
        """Release/version the source reports, or None when unknown."""

    @abstractmethod
    async def health_check(self) -> ConnectorHealth:
        """Verifies the source is reachable and behaving."""

    @abstractmethod
    async def fetch(self, request: object) -> object:
        """Fetches typed data from the source for one request."""

    async def close(self) -> None:
        """Releases any resources owned by the connector (no-op by default)."""
