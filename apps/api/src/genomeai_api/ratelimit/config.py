from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WindowSize(StrEnum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass(frozen=True)
class RateLimitRule:
    max_requests: int
    window_seconds: int
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_requests < 0:
            raise ValueError("max_requests must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")


@dataclass(frozen=True)
class TokenLimitRule:
    max_tokens: int
    window_seconds: int
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.max_tokens < 0:
            raise ValueError("max_tokens must be >= 0")
        if self.window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")


@dataclass(frozen=True)
class RateLimitConfig:
    enabled: bool = True

    global_requests_per_minute: int = 60
    global_requests_per_hour: int = 1000
    global_requests_per_day: int = 10000

    per_endpoint_requests_per_minute: int = 30
    per_endpoint_requests_per_hour: int = 500

    burst_size: int = 10
    burst_window_seconds: int = 1

    ai_tokens_per_minute: int = 100_000
    ai_tokens_per_hour: int = 1_000_000
    ai_tokens_per_day: int = 5_000_000

    ai_requests_per_minute: int = 20
    ai_requests_per_hour: int = 500
    ai_requests_per_day: int = 3000

    def __post_init__(self) -> None:
        for field_name in [
            "global_requests_per_minute",
            "global_requests_per_hour",
            "global_requests_per_day",
            "per_endpoint_requests_per_minute",
            "per_endpoint_requests_per_hour",
            "burst_size",
            "ai_tokens_per_minute",
            "ai_tokens_per_hour",
            "ai_tokens_per_day",
            "ai_requests_per_minute",
            "ai_requests_per_hour",
            "ai_requests_per_day",
        ]:
            val = getattr(self, field_name)
            if val < 0:
                raise ValueError(f"{field_name} must be >= 0, got {val}")
        if self.burst_window_seconds <= 0:
            raise ValueError("burst_window_seconds must be > 0")

    @classmethod
    def disabled(cls) -> RateLimitConfig:
        return cls(enabled=False)

    @classmethod
    def from_env(cls, prefix: str = "GENOMEAI_RATELIMIT_") -> RateLimitConfig:
        import os

        def _int(key: str, default: int) -> int:
            val = os.environ.get(f"{prefix}{key}")
            return int(val) if val is not None else default

        def _bool(key: str, default: bool) -> bool:
            val = os.environ.get(f"{prefix}{key}")
            if val is None:
                return default
            return val.lower() in ("1", "true", "yes")

        return cls(
            enabled=_bool("ENABLED", True),
            global_requests_per_minute=_int("GLOBAL_RPM", 60),
            global_requests_per_hour=_int("GLOBAL_RPH", 1000),
            global_requests_per_day=_int("GLOBAL_RPD", 10000),
            per_endpoint_requests_per_minute=_int("ENDPOINT_RPM", 30),
            per_endpoint_requests_per_hour=_int("ENDPOINT_RPH", 500),
            burst_size=_int("BURST_SIZE", 10),
            burst_window_seconds=_int("BURST_WINDOW", 1),
            ai_tokens_per_minute=_int("AI_TPM", 100_000),
            ai_tokens_per_hour=_int("AI_TPH", 1_000_000),
            ai_tokens_per_day=_int("AI_TPD", 5_000_000),
            ai_requests_per_minute=_int("AI_RPM", 20),
            ai_requests_per_hour=_int("AI_RPH", 500),
            ai_requests_per_day=_int("AI_RPD", 3000),
        )
