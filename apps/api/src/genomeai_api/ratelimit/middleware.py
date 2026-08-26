from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from genomeai_api.ratelimit.config import RateLimitConfig
from genomeai_api.ratelimit.limiter import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        limiter: RateLimiter,
        config: RateLimitConfig | None = None,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._config = config or RateLimitConfig()

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if not self._config.enabled:
            return await call_next(request)

        if request.url.path in ("/health", "/ready", "/live", "/", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        identifier = f"{client_ip}:{user_agent[:50]}"

        rpm_result = await self._limiter.check_sliding_window(
            "global",
            identifier,
            self._config.global_requests_per_minute,
            60,
        )
        if not rpm_result.allowed:
            return self._rate_limit_response(
                rpm_result.limit,
                rpm_result.remaining,
                rpm_result.retry_after_seconds,
                rpm_result.reset_at,
                "global_minute",
            )

        rph_result = await self._limiter.check_sliding_window(
            "global_hour",
            identifier,
            self._config.global_requests_per_hour,
            3600,
        )
        if not rph_result.allowed:
            return self._rate_limit_response(
                rph_result.limit,
                rph_result.remaining,
                rph_result.retry_after_seconds,
                rph_result.reset_at,
                "global_hour",
            )

        endpoint = f"{request.method}:{request.url.path}"
        ep_rpm = await self._limiter.check_sliding_window(
            "endpoint",
            f"{identifier}:{endpoint}",
            self._config.per_endpoint_requests_per_minute,
            60,
        )
        if not ep_rpm.allowed:
            return self._rate_limit_response(
                ep_rpm.limit,
                ep_rpm.remaining,
                ep_rpm.retry_after_seconds,
                ep_rpm.reset_at,
                "endpoint_minute",
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit-Minute"] = str(self._config.global_requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(rpm_result.remaining)
        response.headers["X-RateLimit-Limit-Hour"] = str(self._config.global_requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(rph_result.remaining)

        if rpm_result.reset_at:
            response.headers["X-RateLimit-Reset"] = str(int(rpm_result.reset_at))

        return response

    @staticmethod
    def _rate_limit_response(
        limit: int,
        remaining: int,
        retry_after: float | None,
        reset_at: float | None,
        scope: str,
    ) -> JSONResponse:
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Scope": scope,
        }
        if retry_after is not None:
            headers["Retry-After"] = str(int(retry_after) + 1)
        if reset_at is not None:
            headers["X-RateLimit-Reset"] = str(int(reset_at))

        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded for {scope}",
                "retry_after_seconds": retry_after,
                "limit": limit,
                "remaining": remaining,
            },
            headers=headers,
        )
