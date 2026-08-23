"""Error hierarchy for the Data Integration Foundation.

All integration errors derive from a single `IntegrationError` base so callers
can catch one type, and every error carries structured, machine-readable fields
that never include credentials or raw payloads.
"""

from __future__ import annotations

from genomeai_shared import BaseError


class IntegrationError(BaseError):
    """Base for every Data Integration Foundation error."""

    error_code: str = "integration.error"


class DataSourceNotFoundError(IntegrationError):
    error_code = "integration.source-not-found"

    def __init__(self, source_id: str) -> None:
        super().__init__(
            message=f"Data source '{source_id}' is not registered",
            detail="No data source is registered under this stable source id",
        )


class ConnectorNotFoundError(IntegrationError):
    error_code = "integration.connector-not-found"

    def __init__(self, source_id: str) -> None:
        super().__init__(
            message=f"Connector for '{source_id}' is not available",
            detail="No connector implementation is registered for this data source.",
        )


class IncompatibleConnectorError(IntegrationError):
    error_code = "integration.connector-incompatible"

    def __init__(self, source_id: str, reason: str) -> None:
        super().__init__(
            message=f"Connector for '{source_id}' is incompatible: {reason}",
            detail="The registered connector cannot be used for this data source.",
        )


class InvalidJobTransitionError(IntegrationError):
    error_code = "integration.job-invalid-transition"

    def __init__(self, current: str, next_state: str) -> None:
        super().__init__(
            message=f"Cannot transition ingestion job from '{current}' to '{next_state}'",
            detail="The ingestion job state machine does not allow this transition.",
        )


class IntegrationConfigurationError(IntegrationError):
    error_code = "integration.configuration-error"


class UnsafeSourceUrlError(IntegrationError):
    error_code = "integration.unsafe-url"

    def __init__(self, url: str) -> None:
        super().__init__(
            message="Refusing to fetch an unsafe external URL",
            detail=f"The URL '{url}' is not allowed by the integration allowlist.",
        )


class FetcherError(IntegrationError):
    """Structured error raised by the fetcher layer on non-2xx HTTP responses."""

    error_code = "integration.fetcher-error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message=message, detail=self._detail())

    def _detail(self) -> str | None:
        if self.status_code is None:
            return None
        return f"External source responded with status {self.status_code}"


class FetchTimeoutError(FetcherError):
    error_code = "integration.fetcher-timeout"


class FetcherTransportError(FetcherError):
    """Unrecoverable transport failure (DNS, connection refused, TLS, etc.)."""

    error_code = "integration.fetcher-transport"


class NormalizationError(IntegrationError):
    """An external record could not be normalized into canonical form."""

    error_code = "integration.normalization-error"


__all__ = [
    "ConnectorNotFoundError",
    "DataSourceNotFoundError",
    "FetchTimeoutError",
    "FetcherError",
    "FetcherTransportError",
    "IncompatibleConnectorError",
    "IntegrationConfigurationError",
    "IntegrationError",
    "InvalidJobTransitionError",
    "NormalizationError",
    "UnsafeSourceUrlError",
]
