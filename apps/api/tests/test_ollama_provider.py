"""Tests for Ollama AI provider — REAL API calls.

These tests hit the actual Ollama server (localhost:11434).
If Ollama is not running, tests are skipped.
"""

import pytest

from genomeai_api.ai.ollama import OllamaProvider
from genomeai_api.ai.base import AIRequest


@pytest.fixture
def ollama() -> OllamaProvider:
    return OllamaProvider()


class TestOllamaProvider:
    """Tests for Ollama with REAL API calls."""

    @pytest.mark.asyncio
    async def test_health_check(self, ollama: OllamaProvider) -> None:
        """Check if Ollama is running."""
        ok = await ollama.health_check()
        if not ok:
            pytest.skip("Ollama not running — install and start Ollama")
        assert ok is True

    @pytest.mark.asyncio
    async def test_list_models(self, ollama: OllamaProvider) -> None:
        """List available Ollama models."""
        ok = await ollama.health_check()
        if not ok:
            pytest.skip("Ollama not running")
        models = await ollama.list_models()
        assert len(models) > 0

    @pytest.mark.asyncio
    async def test_generate_simple(self, ollama: OllamaProvider) -> None:
        """Generate a simple response from Ollama."""
        ok = await ollama.health_check()
        if not ok:
            pytest.skip("Ollama not running")
        request = AIRequest(
            prompt="What is 2 + 2? Reply with just the number.",
            max_tokens=10,
            temperature=0.0,
        )
        response = await ollama.generate(request)
        assert response.text
        assert response.provider == "ollama"
        assert "4" in response.text

    @pytest.mark.asyncio
    async def test_generate_gene_analysis(self, ollama: OllamaProvider) -> None:
        """Test AI can analyze gene data."""
        ok = await ollama.health_check()
        if not ok:
            pytest.skip("Ollama not running")
        request = AIRequest(
            prompt=(
                "Analyze the BRCA1 gene. "
                "What is its function? Reply in one sentence."
            ),
            max_tokens=100,
            temperature=0.3,
        )
        response = await ollama.generate(request)
        assert response.text
        assert len(response.text) > 10
