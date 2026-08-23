from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from genomeai_api.integration.connectors.fetcher import (
    FetchRequest,
    HttpFetcher,
    build_public_url,
    validate_allowed_url,
)
from genomeai_api.integration.errors import (
    FetcherError,
    FetchTimeoutError,
    UnsafeSourceUrlError,
)

ALLOWED = ["https://api.example.com"]


def _transport(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://api.example.com/data",
        "https://evil.example.com/path",
        "http://169.254.169.254/latest/meta-data",
        "",
    ],
)
def test_validate_allowed_url_rejects_unlisted_targets(url: str) -> None:
    with pytest.raises(UnsafeSourceUrlError):
        validate_allowed_url(url, ALLOWED)


def test_empty_allowlist_refuses_everything() -> None:
    with pytest.raises(UnsafeSourceUrlError):
        validate_allowed_url("https://api.example.com", [])


def test_allowlist_accepts_exact_and_subpath_matches() -> None:
    assert validate_allowed_url("https://api.example.com", ALLOWED) == "https://api.example.com"
    assert (
        validate_allowed_url("https://api.example.com/v1/records", ALLOWED)
        == "https://api.example.com/v1/records"
    )


def test_prefix_match_does_not_cross_host_boundary() -> None:
    with pytest.raises(UnsafeSourceUrlError):
        validate_allowed_url("https://api.example.com.evil.io/x", ALLOWED)


def test_build_public_url_joins_paths() -> None:
    base = build_public_url("https://api.example.com", "/reference/records")
    assert base == "https://api.example.com/reference/records"
    assert build_public_url("https://api.example.com/", "") == "https://api.example.com"


@pytest.mark.asyncio
async def test_fetch_sends_params_and_headers() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["accept"] = request.headers.get("accept")
        return httpx.Response(200, json={"ok": True})

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        result = await fetcher.fetch(
            FetchRequest(
                path="/reference/records",
                params={"page": 2},
                headers={"Accept": "application/json"},
            )
        )

    assert seen["url"] == "https://api.example.com/reference/records?page=2"
    assert seen["accept"] == "application/json"
    assert result.ok is True
    assert result.payload == {"ok": True}
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_fetch_http_failure_raises_structured_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "missing"})

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        with pytest.raises(FetcherError) as exc_info:
            await fetcher.fetch(FetchRequest(path="/missing"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.retryable is False


@pytest.mark.asyncio
async def test_retries_disabled_by_default() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503)

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        with pytest.raises(FetcherError):
            await fetcher.fetch(FetchRequest(path="/flaky"))
    assert calls["n"] == 1


class _NoSleep:
    """Avoids real sleeping while still counting retry backoffs."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, seconds: float) -> None:  # pragma: no cover - trivial
        self.calls += 1
        assert 0.05 <= seconds <= 5.0


@pytest.mark.asyncio
async def test_opt_in_retry_respects_bound_and_gives_up(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500)

    sleeper = _NoSleep()
    monkeypatch.setattr(asyncio, "sleep", sleeper)

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            default_max_retries=2,
            client=client,
        )
        with pytest.raises(FetcherError) as exc_info:
            await fetcher.fetch(FetchRequest(path="/flaky"))

    # 1 initial + 2 retries, then a structured error.
    assert calls["n"] == 3
    assert exc_info.value.retryable is True
    assert sleeper.calls == 2


@pytest.mark.asyncio
async def test_success_after_one_retry_reports_retries_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"recovered": True})

    async def instant_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", instant_sleep)

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            default_max_retries=1,
            client=client,
        )
        result = await fetcher.fetch(FetchRequest(path="/flaky"))
    assert result.ok is True
    assert result.retries == 1


@pytest.mark.asyncio
async def test_rate_limit_metadata_parsed_from_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "X-RateLimit-Limit": "10",
                "X-RateLimit-Remaining": "7",
                "Retry-After": "3",
                "content-type": "application/json",
            },
            content=json.dumps({"ok": True}).encode(),
        )

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        result = await fetcher.fetch(FetchRequest(path="/records"))
    assert result.rate_limit.observed is True
    assert result.rate_limit.remaining == 7
    assert result.rate_limit.retry_after_seconds == 3.0


@pytest.mark.asyncio
async def test_timeout_raises_timeout_error() -> None:
    def raise_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    async with _transport(raise_timeout) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        with pytest.raises(FetchTimeoutError):
            await fetcher.fetch(FetchRequest(path="/slow"))


@pytest.mark.asyncio
async def test_cancellation_propagates() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        await asyncio.sleep(10)
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)
    fetcher = HttpFetcher(
        "https://api.example.com",
        allowed_source_urls=ALLOWED,
        client=httpx.AsyncClient(transport=transport),
    )
    task = asyncio.get_running_loop().create_task(fetcher.fetch(FetchRequest(path="/x")))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_unsafe_base_url_rejected_at_construction() -> None:
    with pytest.raises(UnsafeSourceUrlError):
        HttpFetcher("https://not-allowed.example.com", allowed_source_urls=ALLOWED)


@pytest.mark.asyncio
async def test_non_json_content_returned_as_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain-data")

    async with _transport(handler) as client:
        fetcher = HttpFetcher(
            "https://api.example.com",
            allowed_source_urls=ALLOWED,
            client=client,
        )
        result = await fetcher.fetch(FetchRequest(path="/text"))
    assert result.payload == "plain-data"
