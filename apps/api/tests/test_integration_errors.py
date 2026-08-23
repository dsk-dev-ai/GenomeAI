from __future__ import annotations

import pytest
from genomeai_api.integration.errors import (
    ConnectorNotFoundError,
    DataSourceNotFoundError,
    FetcherError,
    FetcherTransportError,
    FetchTimeoutError,
    IncompatibleConnectorError,
    IntegrationConfigurationError,
    IntegrationError,
    InvalidJobTransitionError,
    NormalizationError,
    UnsafeSourceUrlError,
)
from genomeai_shared import BaseError


@pytest.mark.parametrize(
    "error",
    [
        DataSourceNotFoundError("x"),
        ConnectorNotFoundError("x"),
        IncompatibleConnectorError("x", "reason"),
        InvalidJobTransitionError("pending", "succeeded"),
        IntegrationConfigurationError("bad config"),
        UnsafeSourceUrlError("file:///etc/passwd"),
        FetcherError("boom", status_code=500),
        FetchTimeoutError("slow"),
        FetcherTransportError("dns"),
        NormalizationError("bad record"),
    ],
)
def test_all_integration_errors_share_base(error: IntegrationError) -> None:
    assert isinstance(error, BaseError)
    assert isinstance(error, IntegrationError)
    assert error.error_code.startswith("integration.")


def test_fetcher_error_carries_structured_status() -> None:
    err = FetcherError("boom", status_code=503, retryable=True)
    assert err.status_code == 503
    assert err.retryable is True


def test_error_messages_do_not_include_credentials() -> None:
    secret = "super-secret-token"
    err = UnsafeSourceUrlError(f"https://user:{secret}@example.com")
    assert secret not in str(err)
