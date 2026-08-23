"""Reusable HTTP fetcher for scientific data sources.

The fetcher is the only component in the integration layer that performs
network I/O over the wire. It enforces the SSRF allowlist, surfaces structured
errors, respects explicit timeouts, honors cancellation, and exposes
rate-limit metadata for future policies — it does **not** silently retry
aggressively (retries are opt-in, bounded, and only for retryable statuses).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse, urlunparse

import httpx

from genomeai_api.integration.errors import (
    FetcherError,
    FetcherTransportError,
    FetchTimeoutError,
    UnsafeSourceUrlError,
)

HTTPMethod = Literal["GET", "POST"]

# Status codes the fetcher considers retryable (only when retries are enabled).
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

_RATE_LIMIT_LIMIT_HEADERS = ("x-ratelimit-limit", "x-rate-limit-limit")
_RATE_LIMIT_REMAINING_HEADERS = ("x-ratelimit-remaining", "x-rate-limit-remaining")
_RATE_LIMIT_RESET_HEADERS = ("x-ratelimit-reset", "x-rate-limit-reset")


@dataclass(frozen=True)
class FetchRequest:
    """A single outbound HTTP request against a source's base URL."""

    path: str
    method: HTTPMethod = "GET"
    params: dict[str, str | int] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: object | None = None
    timeout_seconds: float | None = None
    max_retries: int | None = None


@dataclass(frozen=True)
class RateLimitMetadata:
    """Rate-limit observations surfaced for future throttling policies."""

    observed: bool = False
    requests_per_second: float | None = None
    remaining: int | None = None
    reset_at: str | None = None
    retry_after_seconds: float | None = None


@dataclass(frozen=True)
class FetchResult:
    """Normalized result of one fetch, with retry/rate metadata."""

    status_code: int
    ok: bool
    payload: object
    url: str
    elapsed_ms: int
    retries: int = 0
    rate_limit: RateLimitMetadata = field(default_factory=RateLimitMetadata)


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def validate_allowed_url(base_url: str, allowed_base_urls: Sequence[str]) -> str:
    """Fail-closed SSRF check: base URL must be an allowed HTTP(S) origin.

    Returns the normalized base URL (trailing slash removed). Rejects anything
    that is not ``http``/``https`` or that does not start with an allowlisted
    prefix. An empty allowlist refuses everything — connections are *opt-in*.
    """
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeSourceUrlError(base_url)
    if not parsed.netloc:
        raise UnsafeSourceUrlError(base_url)

    normalized = base_url.rstrip("/")
    for allowed in allowed_base_urls:
        clean = allowed.rstrip("/")
        if clean and (normalized == clean or normalized.startswith(clean + "/")):
            return normalized

    raise UnsafeSourceUrlError(base_url)


def build_public_url(base_url: str, path: str) -> str:
    """Composes a full URL from an allowlisted base and a path (never user-url)."""
    base = base_url.rstrip("/")
    trimmed = path.strip("/")
    if not trimmed:
        return base
    parsed = urlparse(base)
    path_section = f"{parsed.path.rstrip('/')}/{trimmed}" if parsed.path else f"/{trimmed}"
    return urlunparse((parsed.scheme, parsed.netloc, path_section, "", "", ""))


class HttpFetcher:
    """Async fetcher bound to one source base URL, behind the allowlist.

    ``allowed_source_urls`` is the SSRF allowlist and ``base_url`` must match
    it. A caller may inject an httpx client for tests to avoid all real
    network I/O.
    """

    def __init__(
        self,
        base_url: str,
        *,
        allowed_source_urls: Sequence[str],
        request_timeout_seconds: float = 30.0,
        default_max_retries: int = 0,
        client: httpx.AsyncClient | None = None,
        logger_: logging.Logger | None = None,
    ) -> None:
        self._base_url = validate_allowed_url(base_url, allowed_source_urls)
        self._request_timeout_seconds = request_timeout_seconds
        self._default_max_retries = max(0, default_max_retries)
        self._logger = logger_ or logging.getLogger(__name__)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(request_timeout_seconds),
            follow_redirects=False,
        )

    @property
    def base_url(self) -> str:
        return self._base_url

    async def fetch(self, request: FetchRequest) -> FetchResult:
        url = build_public_url(self._base_url, request.path)
        timeout = request.timeout_seconds or self._request_timeout_seconds
        max_retries = (
            self._default_max_retries
            if request.max_retries is None
            else max(0, request.max_retries)
        )

        attempts = 0
        while True:
            attempts += 1
            started = asyncio.get_running_loop().time()
            try:
                response = await self._client.request(
                    request.method,
                    url,
                    params=request.params,
                    headers=request.headers,
                    json=request.body if request.method == "POST" else None,
                    timeout=timeout,
                )
            except asyncio.CancelledError:
                raise
            except httpx.TimeoutException as exc:
                raise FetchTimeoutError(
                    f"Timed out fetching {url} after {timeout:g}s",
                    retryable=True,
                ) from exc
            except httpx.HTTPError as exc:
                raise FetcherTransportError(
                    f"Transport error fetching {url}: {exc.__class__.__name__}",
                ) from exc

            elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)

            retryable = (
                response.status_code in RETRYABLE_STATUS_CODES and attempts <= max_retries
            )
            if not response.is_success and retryable:
                self._logger.warning(
                    "retry %s/%s after status %s for %s %s",
                    attempts,
                    max_retries,
                    response.status_code,
                    request.method,
                    url,
                )
                await self._retry_delay(response)
                continue

            if response.status_code == 204:
                payload: object = None
            else:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    payload = self._parse_json(response, url)
                else:
                    payload = response.text

            if not response.is_success:
                raise FetcherError(
                    f"External source returned HTTP {response.status_code} for {url}",
                    status_code=response.status_code,
                    retryable=response.status_code in RETRYABLE_STATUS_CODES,
                )

            return FetchResult(
                status_code=response.status_code,
                ok=True,
                payload=payload,
                url=url,
                elapsed_ms=elapsed_ms,
                retries=attempts - 1,
                rate_limit=self._read_rate_limit(response),
            )

    async def _retry_delay(self, response: httpx.Response) -> None:
        retry_after = _float_or_none(response.headers.get("retry-after"))
        backoff = 1.0 if retry_after is None else retry_after
        await asyncio.sleep(min(max(backoff, 0.05), 5.0))

    def _parse_json(self, response: httpx.Response, url: str) -> object:
        try:
            return response.json()
        except ValueError as exc:
            raise FetcherError(
                f"External source at {url} returned non-JSON content",
                status_code=response.status_code,
            ) from exc

    def _read_rate_limit(self, response: httpx.Response) -> RateLimitMetadata:
        headers = response.headers
        remaining: int | None = None
        limit: int | None = None
        reset: str | None = None
        for name in _RATE_LIMIT_REMAINING_HEADERS:
            value = headers.get(name)
            if value is not None:
                remaining = _int_or_none(value)
                break
        for name in _RATE_LIMIT_LIMIT_HEADERS:
            value = headers.get(name)
            if value is not None:
                limit = _int_or_none(value)
                break
        for name in _RATE_LIMIT_RESET_HEADERS:
            value = headers.get(name)
            if value is not None:
                reset = value
                break
        retry_after = _float_or_none(headers.get("retry-after"))
        observed = any(value is not None for value in (remaining, limit, reset, retry_after))
        return RateLimitMetadata(
            observed=observed,
            requests_per_second=float(limit) if limit is not None else None,
            remaining=remaining,
            reset_at=reset,
            retry_after_seconds=retry_after,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
