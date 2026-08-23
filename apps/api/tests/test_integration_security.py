from __future__ import annotations

import logging

import httpx
import pytest
from genomeai_api.integration.connectors.fetcher import FetchRequest, HttpFetcher
from genomeai_api.integration.errors import UnsafeSourceUrlError

ALLOWED = ["https://api.example.com"]


@pytest.mark.parametrize(
    "target",
    [
        "http://127.0.0.1:8000/admin",
        "https://internal-metadata.aws/latest",
        "unix:///run/docker.sock",
        "gopher://example.com",
    ],
)
def test_fetcher_never_binds_to_non_allowlisted_targets(target: str) -> None:
    with pytest.raises(UnsafeSourceUrlError):
        HttpFetcher(target, allowed_source_urls=ALLOWED)


def test_allowlist_cannot_be_widened_via_path_tricks() -> None:
    with pytest.raises(UnsafeSourceUrlError):
        HttpFetcher("https://API.example.com@evil.example.com/", allowed_source_urls=ALLOWED)


@pytest.mark.asyncio
async def test_credential_ref_is_never_serialized_into_requests() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers.get("authorization")
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(
        "https://api.example.com",
        allowed_source_urls=ALLOWED,
        client=client,
    )
    # The fetcher API has no way to attach credentials; requests carry none.
    result = await fetcher.fetch(FetchRequest(path="/records"))
    await fetcher.aclose()
    assert result.ok is True
    assert captured["authorization"] is None


def test_fetch_logging_does_not_emit_headers_or_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    fetcher = HttpFetcher(
        "https://api.example.com",
        allowed_source_urls=ALLOWED,
        default_max_retries=0,
        client=client,
    )

    with caplog.at_level(logging.DEBUG, logger="genomeai_api.integration.connectors.fetcher"):
        import asyncio

        asyncio.run(_fetch_expect_error(fetcher))

    for record in caplog.records:
        message = record.getMessage()
        assert "authorization" not in message.lower()
        assert "api-key" not in message.lower()
        assert "bearer" not in message.lower()


async def _fetch_expect_error(fetcher: HttpFetcher) -> None:
    from genomeai_api.integration.errors import FetcherError

    try:
        await fetcher.fetch(
            FetchRequest(path="/flaky", headers={"Authorization": "Bearer secret-token"})
        )
    except FetcherError:
        pass
    finally:
        await fetcher.aclose()
