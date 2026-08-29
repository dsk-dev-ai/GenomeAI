"""Tests for gene analysis engine — REAL NCBI + REAL Ollama.

These tests use real NCBI API calls and real Ollama inference.
Requires a local Ollama server; if it is not running the real-data tests
are skipped. Transient NCBI connectivity failures skip gracefully rather
than failing CI (matching the connector-test flake handling).
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse
from genomeai_api.ai.ollama import OLLAMA_DEFAULT_BASE_URL, OllamaProvider
from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.services.gene_analysis import GeneAnalysisEngine

OLLAMA_TAGS_URL = f"{OLLAMA_DEFAULT_BASE_URL}/api/tags"


def _is_transient(exc: Exception) -> bool:
    """Return True if the exception is a transient network/server error."""
    msg = str(exc).lower()
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status >= 500 or status == 429:
            return True
    return any(
        kw in msg
        for kw in (
            "connection",
            "connect",
            "timeout",
            "name or service not known",
            "dns",
            "remote",
            "incomplete",
            "server error",
        )
    )


def _retry_transient(retries: int = 1, delay: float = 3.0) -> Callable[..., Any]:
    """Decorator: retry an async function, then skip on transient outages."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(max(1, retries)):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    if not _is_transient(exc):
                        raise
                    last_exc = exc
                    if attempt < retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            pytest.skip(f"External API unavailable after {retries} retries: {last_exc}")

        return wrapper

    return decorator


def _ollama_available() -> bool:
    """Return True if the local Ollama server is reachable (short timeout)."""
    try:
        response = httpx.get(OLLAMA_TAGS_URL, timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def engine() -> GeneAnalysisEngine:
    return GeneAnalysisEngine(
        ai_provider=OllamaProvider(),
        ncbi_client=NCBIClient(),
    )


@pytest.mark.skipif(
    not _ollama_available(),
    reason="Local Ollama server not running; skipping real-data gene analysis tests",
)
@pytest.mark.asyncio
class TestGeneAnalysisEngine:
    """Tests for gene analysis with REAL data (requires local Ollama)."""

    @_retry_transient()
    async def test_analyze_brca1(self, engine: GeneAnalysisEngine) -> None:
        """Analyze BRCA1 gene — verify returns structured analysis."""
        analysis = await engine.analyze_by_symbol("BRCA1")
        assert analysis.gene_symbol == "BRCA1"
        assert analysis.gene_id == "672"
        assert analysis.name
        assert analysis.organism == "Homo sapiens"
        assert analysis.source in ("ncbi", "ncbi+ollama")

    @_retry_transient()
    async def test_analyze_tp53(self, engine: GeneAnalysisEngine) -> None:
        """Analyze TP53 gene — verify returns structured analysis."""
        analysis = await engine.analyze_by_symbol("TP53")
        assert analysis.gene_symbol == "TP53"
        assert analysis.gene_id == "7157"
        assert analysis.name

    @_retry_transient()
    async def test_analyze_by_id(self, engine: GeneAnalysisEngine) -> None:
        """Analyze BRCA1 by Gene ID 672 — verify returns correct gene."""
        analysis = await engine.analyze_by_id("672")
        assert analysis.gene_symbol == "BRCA1"
        assert analysis.gene_id == "672"

    @_retry_transient()
    async def test_analyze_nonexistent_gene(
        self, engine: GeneAnalysisEngine
    ) -> None:
        """Analyze nonexistent gene — verify raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            await engine.analyze_by_symbol("XYZNONEXISTENT123")


class FailingAI(AIProvider):
    """AI provider that always raises, to exercise the fallback deterministically."""

    name = "failing"

    async def generate(self, request: AIRequest) -> AIResponse:
        raise RuntimeError("ai unavailable")

    async def health_check(self) -> bool:
        return False

    async def list_models(self) -> list[str]:
        return []


@pytest.mark.asyncio
async def test_basic_analysis_without_ai() -> None:
    """Test basic analysis without AI (fallback mode), no Ollama required."""
    from genomeai_api.integration.connectors.ncbi.models import NCBIGeneRecord

    record = NCBIGeneRecord(
        gene_id="672",
        symbol="BRCA1",
        name="BRCA1 DNA repair associated",
        organism="Homo sapiens",
        chromosome="17",
        map_location="17q21.31",
    )
    engine = GeneAnalysisEngine(
        ai_provider=FailingAI(),
        ncbi_client=NCBIClient(),
    )
    analysis = await engine.analyze_from_record(record)
    assert analysis.gene_symbol == "BRCA1"
    assert analysis.gene_id == "672"
    assert analysis.source == "ncbi"
