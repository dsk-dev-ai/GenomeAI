from __future__ import annotations

import time
from dataclasses import dataclass

from redis.asyncio import Redis


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: float | None = None
    reset_at: float | None = None


class RateLimiter:
    def __init__(self, redis: Redis | None, key_prefix: str = "ratelimit") -> None:
        self._redis = redis
        self._key_prefix = key_prefix

    def _make_key(self, namespace: str, identifier: str, window: str) -> str:
        return f"{self._key_prefix}:{namespace}:{identifier}:{window}"

    async def check_sliding_window(
        self,
        namespace: str,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> RateLimitResult:
        if self._redis is None:
            return RateLimitResult(allowed=True, limit=max_requests, remaining=max_requests)

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        key = self._make_key(namespace, identifier, str(window_start))

        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds * 2)
        results = await pipe.execute()

        current_count: int = results[0]
        remaining = max(0, max_requests - current_count)
        allowed = current_count <= max_requests
        reset_at = float(window_start + window_seconds)
        retry_after = None if allowed else float(window_seconds - (now - window_start))

        return RateLimitResult(
            allowed=allowed,
            limit=max_requests,
            remaining=remaining,
            retry_after_seconds=retry_after,
            reset_at=reset_at,
        )

    async def check_token_bucket(
        self,
        namespace: str,
        identifier: str,
        max_tokens: int,
        refill_rate: float,
    ) -> RateLimitResult:
        if self._redis is None:
            return RateLimitResult(allowed=True, limit=max_tokens, remaining=max_tokens)

        now = time.time()
        key = self._make_key(namespace, identifier, "bucket")

        script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_refill = tonumber(bucket[2]) or now

        local elapsed = now - last_refill
        tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

        if tokens >= requested then
            tokens = tokens - requested
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
            return {1, tokens, 0}
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
            redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) * 2)
            local wait = (requested - tokens) / refill_rate
            return {0, tokens, wait}
        end
        """

        result = await self._redis.eval(  # type: ignore[no-untyped-call]
            script,
            1,
            key,
            str(max_tokens),
            str(refill_rate),
            str(now),
            "1",
        )

        allowed = bool(result[0])
        remaining = int(result[1])
        retry_after = float(result[2]) if result[2] else None

        return RateLimitResult(
            allowed=allowed,
            limit=max_tokens,
            remaining=remaining,
            retry_after_seconds=retry_after,
        )

    async def increment_counter(
        self,
        namespace: str,
        identifier: str,
        window_seconds: int,
        amount: int = 1,
    ) -> int:
        if self._redis is None:
            return amount

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        key = self._make_key(namespace, identifier, str(window_start))

        pipe = self._redis.pipeline()
        pipe.incrby(key, amount)
        pipe.expire(key, window_seconds * 2)
        results = await pipe.execute()

        return int(results[0])

    async def get_counter(
        self,
        namespace: str,
        identifier: str,
        window_seconds: int,
    ) -> int:
        if self._redis is None:
            return 0

        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        key = self._make_key(namespace, identifier, str(window_start))

        value = await self._redis.get(key)
        return int(value) if value else 0

    async def reset(self, namespace: str, identifier: str) -> int:
        if self._redis is None:
            return 0

        pattern = f"{self._key_prefix}:{namespace}:{identifier}:*"
        keys: list[str | bytes] = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)  # type: ignore[arg-type]

        if keys:
            return await self._redis.delete(*keys)
        return 0

    async def reset_all(self) -> int:
        if self._redis is None:
            return 0

        pattern = f"{self._key_prefix}:*"
        keys: list[str | bytes] = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)  # type: ignore[arg-type]

        if keys:
            return await self._redis.delete(*keys)
        return 0
