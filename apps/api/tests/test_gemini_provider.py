"""Tests for Gemini provider configuration and lifecycle."""

from __future__ import annotations

import pytest
from genomeai_api.ai.gemini import DEFAULT_GEMINI_MODEL, GeminiProvider


def test_uses_google_api_key_before_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.delenv("GENOMEAI_GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    provider = GeminiProvider()

    assert provider._api_key == "google-key"
    assert provider._default_model == DEFAULT_GEMINI_MODEL


def test_model_can_be_configured_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom")
    monkeypatch.setenv("GENOMEAI_GEMINI_MODEL", "genomeai-custom")

    provider = GeminiProvider()

    assert provider._default_model == "genomeai-custom"


@pytest.mark.asyncio
async def test_missing_api_key_does_not_create_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    provider = GeminiProvider()

    assert await provider.health_check() is False
    with pytest.raises(RuntimeError, match="Gemini API key is not configured"):
        provider._get_client()


@pytest.mark.asyncio
async def test_close_releases_sync_and_async_clients() -> None:
    calls: list[str] = []

    class FakeAio:
        async def aclose(self) -> None:
            calls.append("aio")

    class FakeClient:
        aio = FakeAio()

        def close(self) -> None:
            calls.append("sync")

    provider = GeminiProvider(api_key="key")
    provider._client = FakeClient()

    await provider.close()

    assert calls == ["sync", "aio"]
    assert provider._client is None
