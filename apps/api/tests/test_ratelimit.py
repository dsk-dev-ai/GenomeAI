from __future__ import annotations

import pytest
from genomeai_api.ratelimit.config import RateLimitConfig
from genomeai_api.ratelimit.controller import LimitController
from genomeai_api.ratelimit.limiter import RateLimiter
from genomeai_api.ratelimit.providers import (
    AIProvider,
    ProviderQuotaManager,
)

pytestmark = pytest.mark.asyncio


class TestRateLimitConfig:
    def test_default_config(self) -> None:
        config = RateLimitConfig()
        assert config.enabled is True
        assert config.global_requests_per_minute == 60
        assert config.global_requests_per_hour == 1000
        assert config.global_requests_per_day == 10000

    def test_disabled_config(self) -> None:
        config = RateLimitConfig.disabled()
        assert config.enabled is False

    def test_invalid_max_requests(self) -> None:
        with pytest.raises(ValueError, match="global_requests_per_minute must be >= 0"):
            RateLimitConfig(global_requests_per_minute=-1)

    def test_from_env_defaults(self) -> None:
        config = RateLimitConfig.from_env(prefix="NONEXISTENT_PREFIX_")
        assert config.enabled is True
        assert config.global_requests_per_minute == 60


class TestRateLimiterInMemory:
    @pytest.fixture
    def limiter(self) -> RateLimiter:
        return RateLimiter(redis=None)

    async def test_sliding_window_no_redis(self, limiter: RateLimiter) -> None:
        result = await limiter.check_sliding_window("test", "id1", 10, 60)
        assert result.allowed is True
        assert result.limit == 10
        assert result.remaining == 10

    async def test_increment_counter_no_redis(self, limiter: RateLimiter) -> None:
        count = await limiter.increment_counter("test", "id1", 60, 5)
        assert count == 5

    async def test_get_counter_no_redis(self, limiter: RateLimiter) -> None:
        count = await limiter.get_counter("test", "id1", 60)
        assert count == 0

    async def test_reset_no_redis(self, limiter: RateLimiter) -> None:
        deleted = await limiter.reset("test", "id1")
        assert deleted == 0

    async def test_reset_all_no_redis(self, limiter: RateLimiter) -> None:
        deleted = await limiter.reset_all()
        assert deleted == 0


class TestProviderQuotaManager:
    @pytest.fixture
    def manager(self) -> ProviderQuotaManager:
        limiter = RateLimiter(redis=None)
        return ProviderQuotaManager(limiter)

    def test_get_default_quota(self, manager: ProviderQuotaManager) -> None:
        quota = manager.get_quota(AIProvider.GEMINI)
        assert quota.provider == AIProvider.GEMINI
        assert quota.requests_per_minute == 10
        assert quota.requests_per_day == 250
        assert quota.enabled is True

    def test_update_quota(self, manager: ProviderQuotaManager) -> None:
        new_quota = manager.update_quota(
            AIProvider.GROQ,
            requests_per_minute=50,
            enabled=False,
        )
        assert new_quota.requests_per_minute == 50
        assert new_quota.enabled is False
        assert manager.get_quota(AIProvider.GROQ).requests_per_minute == 50

    def test_get_all_quotas(self, manager: ProviderQuotaManager) -> None:
        quotas = manager.get_all_quotas()
        assert len(quotas) == 5
        assert AIProvider.OLLAMA in quotas
        assert AIProvider.GEMINI in quotas

    def test_get_available_provider(self, manager: ProviderQuotaManager) -> None:
        provider = manager.get_available_provider()
        assert provider == AIProvider.OLLAMA

    def test_get_available_provider_fallback(self, manager: ProviderQuotaManager) -> None:
        manager.update_quota(AIProvider.OLLAMA, enabled=False)
        provider = manager.get_available_provider()
        assert provider == AIProvider.GEMINI

    def test_get_available_provider_all_disabled(self, manager: ProviderQuotaManager) -> None:
        for p in AIProvider:
            manager.update_quota(p, enabled=False)
        assert manager.get_available_provider() is None

    async def test_check_provider_available_no_redis(self, manager: ProviderQuotaManager) -> None:
        available = await manager.check_provider_available(AIProvider.OLLAMA)
        assert available is True

    async def test_check_provider_disabled(self, manager: ProviderQuotaManager) -> None:
        manager.update_quota(AIProvider.GROQ, enabled=False)
        available = await manager.check_provider_available(AIProvider.GROQ)
        assert available is False

    async def test_record_request_no_redis(self, manager: ProviderQuotaManager) -> None:
        await manager.record_request(AIProvider.GEMINI, tokens_used=100)

    async def test_get_usage_no_redis(self, manager: ProviderQuotaManager) -> None:
        usage = await manager.get_usage(AIProvider.GEMINI)
        assert usage.requests_minute == 0

    async def test_get_all_usage_no_redis(self, manager: ProviderQuotaManager) -> None:
        usage = await manager.get_all_usage()
        assert len(usage) == 5


class TestLimitController:
    @pytest.fixture
    def controller(self) -> LimitController:
        limiter = RateLimiter(redis=None)
        return LimitController(limiter)

    def test_initial_state(self, controller: LimitController) -> None:
        assert controller.is_api_rate_limiting_enabled() is True
        assert controller.is_ai_rate_limiting_enabled() is True

    def test_disable_api_limits(self, controller: LimitController) -> None:
        controller.disable_api_limits()
        assert controller.is_api_rate_limiting_enabled() is False

    def test_enable_api_limits(self, controller: LimitController) -> None:
        controller.disable_api_limits()
        controller.enable_api_limits()
        assert controller.is_api_rate_limiting_enabled() is True

    def test_disable_ai_limits(self, controller: LimitController) -> None:
        controller.disable_ai_limits()
        assert controller.is_ai_rate_limiting_enabled() is False

    def test_disable_all(self, controller: LimitController) -> None:
        controller.disable_all()
        assert controller.is_api_rate_limiting_enabled() is False
        assert controller.is_ai_rate_limiting_enabled() is False

    def test_enable_all(self, controller: LimitController) -> None:
        controller.disable_all()
        controller.enable_all()
        assert controller.is_api_rate_limiting_enabled() is True
        assert controller.is_ai_rate_limiting_enabled() is True

    def test_update_config(self, controller: LimitController) -> None:
        new_config = controller.update_config(global_requests_per_minute=120)
        assert new_config.global_requests_per_minute == 120

    def test_get_config(self, controller: LimitController) -> None:
        config = controller.get_config()
        assert config.global_requests_per_minute == 60

    def test_update_provider_quota(self, controller: LimitController) -> None:
        new_quota = controller.update_provider_quota(
            AIProvider.MISTRAL,
            requests_per_minute=100,
        )
        assert new_quota.requests_per_minute == 100

    def test_enable_disable_provider(self, controller: LimitController) -> None:
        controller.disable_provider(AIProvider.GROQ)
        assert controller.get_provider_quota(AIProvider.GROQ).enabled is False
        controller.enable_provider(AIProvider.GROQ)
        assert controller.get_provider_quota(AIProvider.GROQ).enabled is True

    def test_get_status(self, controller: LimitController) -> None:
        status = controller.get_status()
        assert status["api_rate_limiting"] is True
        assert status["ai_rate_limiting"] is True
        assert "config" in status
        assert "providers" in status
        assert "ollama" in status["providers"]

    def test_audit_log(self, controller: LimitController) -> None:
        controller.disable_api_limits()
        controller.disable_ai_limits()
        log = controller.get_audit_log()
        assert len(log) == 2
        assert log[0]["action"] == "api_limits_disabled"
        assert log[1]["action"] == "ai_limits_disabled"

    async def test_reset_provider(self, controller: LimitController) -> None:
        deleted = await controller.reset_provider(AIProvider.GEMINI)
        assert deleted == 0

    async def test_reset_all(self, controller: LimitController) -> None:
        deleted = await controller.reset_all()
        assert deleted == 0


class TestProviderDefaults:
    def test_ollama_is_unlimited(self) -> None:
        from genomeai_api.ratelimit.providers import DEFAULT_QUOTAS

        ollama = DEFAULT_QUOTAS[AIProvider.OLLAMA]
        assert ollama.requests_per_minute > 100_000
        assert ollama.priority == 0

    def test_priority_order(self) -> None:
        from genomeai_api.ratelimit.providers import DEFAULT_QUOTAS

        priorities = sorted(
            DEFAULT_QUOTAS.items(),
            key=lambda x: x[1].priority,
        )
        assert priorities[0][0] == AIProvider.OLLAMA
        assert priorities[1][0] == AIProvider.GEMINI
        assert priorities[-1][0] == AIProvider.MISTRAL

    def test_all_providers_have_limits(self) -> None:
        from genomeai_api.ratelimit.providers import DEFAULT_QUOTAS

        for provider in AIProvider:
            assert provider in DEFAULT_QUOTAS
            quota = DEFAULT_QUOTAS[provider]
            assert quota.requests_per_minute > 0
            assert quota.requests_per_day > 0
            assert quota.tokens_per_minute > 0
            assert quota.tokens_per_day > 0
