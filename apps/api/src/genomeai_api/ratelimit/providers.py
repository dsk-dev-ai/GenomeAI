from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum

from genomeai_api.ratelimit.limiter import RateLimiter


class AIProvider(StrEnum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    MISTRAL = "mistral"


@dataclass
class ProviderQuota:
    provider: AIProvider
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    tokens_per_day: int
    enabled: bool = True
    priority: int = 0


DEFAULT_QUOTAS: dict[AIProvider, ProviderQuota] = {
    AIProvider.OLLAMA: ProviderQuota(
        provider=AIProvider.OLLAMA,
        requests_per_minute=999_999,
        requests_per_day=999_999,
        tokens_per_minute=999_999,
        tokens_per_day=999_999,
        priority=0,
    ),
    AIProvider.GEMINI: ProviderQuota(
        provider=AIProvider.GEMINI,
        requests_per_minute=10,
        requests_per_day=250,
        tokens_per_minute=250_000,
        tokens_per_day=250_000,
        priority=1,
    ),
    AIProvider.OPENROUTER: ProviderQuota(
        provider=AIProvider.OPENROUTER,
        requests_per_minute=20,
        requests_per_day=50,
        tokens_per_minute=200_000,
        tokens_per_day=500_000,
        priority=2,
    ),
    AIProvider.GROQ: ProviderQuota(
        provider=AIProvider.GROQ,
        requests_per_minute=30,
        requests_per_day=1_000,
        tokens_per_minute=12_000,
        tokens_per_day=500_000,
        priority=3,
    ),
    AIProvider.MISTRAL: ProviderQuota(
        provider=AIProvider.MISTRAL,
        requests_per_minute=20,
        requests_per_day=33_000,
        tokens_per_minute=500_000,
        tokens_per_day=1_000_000,
        priority=4,
    ),
}


@dataclass
class ProviderUsage:
    requests_minute: int = 0
    requests_day: int = 0
    tokens_minute: int = 0
    tokens_day: int = 0
    last_updated: float = field(default_factory=time.time)


class ProviderQuotaManager:
    def __init__(self, limiter: RateLimiter) -> None:
        self._limiter = limiter
        self._quotas = dict(DEFAULT_QUOTAS)

    def get_quota(self, provider: AIProvider) -> ProviderQuota:
        return self._quotas[provider]

    def set_quota(self, provider: AIProvider, quota: ProviderQuota) -> None:
        self._quotas[provider] = quota

    def update_quota(
        self,
        provider: AIProvider,
        *,
        requests_per_minute: int | None = None,
        requests_per_day: int | None = None,
        tokens_per_minute: int | None = None,
        tokens_per_day: int | None = None,
        enabled: bool | None = None,
    ) -> ProviderQuota:
        old = self._quotas[provider]
        rpm = requests_per_minute if requests_per_minute is not None else old.requests_per_minute
        rpd = requests_per_day if requests_per_day is not None else old.requests_per_day
        tpm = tokens_per_minute if tokens_per_minute is not None else old.tokens_per_minute
        tpd = tokens_per_day if tokens_per_day is not None else old.tokens_per_day
        en = enabled if enabled is not None else old.enabled
        new_quota = ProviderQuota(
            provider=provider,
            requests_per_minute=rpm,
            requests_per_day=rpd,
            tokens_per_minute=tpm,
            tokens_per_day=tpd,
            enabled=en,
            priority=old.priority,
        )
        self._quotas[provider] = new_quota
        return new_quota

    def get_all_quotas(self) -> dict[AIProvider, ProviderQuota]:
        return dict(self._quotas)

    def get_available_provider(self) -> AIProvider | None:
        sorted_providers = sorted(
            (q for q in self._quotas.values() if q.enabled),
            key=lambda q: q.priority,
        )
        if not sorted_providers:
            return None
        return sorted_providers[0].provider

    async def check_provider_available(self, provider: AIProvider) -> bool:
        quota = self._quotas.get(provider)
        if quota is None or not quota.enabled:
            return False

        ns = f"ai:{provider.value}"
        rpm = await self._limiter.check_sliding_window(ns, "req", quota.requests_per_minute, 60)
        if not rpm.allowed:
            return False

        rpd = await self._limiter.check_sliding_window(ns, "req_day", quota.requests_per_day, 86400)
        return rpd.allowed

    async def record_request(self, provider: AIProvider, tokens_used: int = 0) -> None:
        ns = f"ai:{provider.value}"
        await self._limiter.increment_counter(ns, "req", 60)
        await self._limiter.increment_counter(ns, "req_day", 86400)
        if tokens_used > 0:
            await self._limiter.increment_counter(ns, "tok", 60, tokens_used)
            await self._limiter.increment_counter(ns, "tok_day", 86400, tokens_used)

    async def get_usage(self, provider: AIProvider) -> ProviderUsage:
        ns = f"ai:{provider.value}"
        return ProviderUsage(
            requests_minute=await self._limiter.get_counter(ns, "req", 60),
            requests_day=await self._limiter.get_counter(ns, "req_day", 86400),
            tokens_minute=await self._limiter.get_counter(ns, "tok", 60),
            tokens_day=await self._limiter.get_counter(ns, "tok_day", 86400),
        )

    async def get_all_usage(self) -> dict[AIProvider, ProviderUsage]:
        return {p: await self.get_usage(p) for p in self._quotas}

    async def reset_provider(self, provider: AIProvider) -> int:
        return await self._limiter.reset("ai", provider.value)

    async def reset_all(self) -> int:
        return await self._limiter.reset_all()
