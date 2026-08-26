from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from genomeai_api.ratelimit.config import RateLimitConfig
from genomeai_api.ratelimit.limiter import RateLimiter
from genomeai_api.ratelimit.providers import (
    AIProvider,
    ProviderQuota,
    ProviderQuotaManager,
    ProviderUsage,
)


@dataclass
class LimitState:
    api_enabled: bool = True
    ai_enabled: bool = True
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    overrides: dict[str, Any] = field(default_factory=dict)


class LimitController:
    def __init__(self, limiter: RateLimiter, config: RateLimitConfig | None = None) -> None:
        self._limiter = limiter
        self._config = config or RateLimitConfig()
        self._state = LimitState(config=self._config)
        self._ai_manager = ProviderQuotaManager(limiter)
        self._audit_log: list[dict[str, Any]] = []

    @property
    def limiter(self) -> RateLimiter:
        return self._limiter

    @property
    def ai_manager(self) -> ProviderQuotaManager:
        return self._ai_manager

    def is_api_rate_limiting_enabled(self) -> bool:
        return self._state.api_enabled

    def is_ai_rate_limiting_enabled(self) -> bool:
        return self._state.ai_enabled

    def enable_api_limits(self) -> None:
        self._state.api_enabled = True
        self._log("api_limits_enabled")

    def disable_api_limits(self) -> None:
        self._state.api_enabled = False
        self._log("api_limits_disabled")

    def enable_ai_limits(self) -> None:
        self._state.ai_enabled = True
        self._log("ai_limits_enabled")

    def disable_ai_limits(self) -> None:
        self._state.ai_enabled = False
        self._log("ai_limits_disabled")

    def enable_all(self) -> None:
        self._state.api_enabled = True
        self._state.ai_enabled = True
        self._log("all_limits_enabled")

    def disable_all(self) -> None:
        self._state.api_enabled = False
        self._state.ai_enabled = False
        self._log("all_limits_disabled")

    def update_config(self, **kwargs: Any) -> RateLimitConfig:
        current = self._state.config
        new_values = {k: v for k, v in kwargs.items() if v is not None}
        self._state.config = RateLimitConfig(**{**current.__dict__, **new_values})
        self._log("config_updated", config=new_values)
        return self._state.config

    def get_config(self) -> RateLimitConfig:
        return self._state.config

    def update_provider_quota(
        self,
        provider: AIProvider,
        **kwargs: Any,
    ) -> ProviderQuota:
        return self._ai_manager.update_quota(provider, **kwargs)

    def get_provider_quota(self, provider: AIProvider) -> ProviderQuota:
        return self._ai_manager.get_quota(provider)

    def get_all_provider_quotas(self) -> dict[AIProvider, ProviderQuota]:
        return self._ai_manager.get_all_quotas()

    def enable_provider(self, provider: AIProvider) -> ProviderQuota:
        return self._ai_manager.update_quota(provider, enabled=True)

    def disable_provider(self, provider: AIProvider) -> ProviderQuota:
        return self._ai_manager.update_quota(provider, enabled=False)

    async def get_provider_usage(self, provider: AIProvider) -> ProviderUsage:
        return await self._ai_manager.get_usage(provider)

    async def get_all_provider_usage(self) -> dict[AIProvider, ProviderUsage]:
        return await self._ai_manager.get_all_usage()

    async def reset_provider(self, provider: AIProvider) -> int:
        return await self._ai_manager.reset_provider(provider)

    async def reset_all(self) -> int:
        return await self._ai_manager.reset_all()

    def get_status(self) -> dict[str, Any]:
        return {
            "api_rate_limiting": self._state.api_enabled,
            "ai_rate_limiting": self._state.ai_enabled,
            "config": self._state.config.__dict__,
            "providers": {
                p.value: {
                    "enabled": q.enabled,
                    "requests_per_minute": q.requests_per_minute,
                    "requests_per_day": q.requests_per_day,
                    "tokens_per_minute": q.tokens_per_minute,
                    "tokens_per_day": q.tokens_per_day,
                    "priority": q.priority,
                }
                for p, q in self._ai_manager.get_all_quotas().items()
            },
        }

    def get_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._audit_log[-limit:]

    def _log(self, action: str, **extra: Any) -> None:
        entry: dict[str, Any] = {
            "timestamp": time.time(),
            "action": action,
        }
        if extra:
            entry["details"] = extra
        self._audit_log.append(entry)
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]
