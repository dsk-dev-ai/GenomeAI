"""Ollama AI provider — local LLM inference, free, unlimited.

Connects to local Ollama server (default: http://localhost:11434).
No API key required. No rate limits. Runs on consumer hardware.
"""

from __future__ import annotations

import logging

import httpx

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"


class OllamaProvider(AIProvider):
    """Ollama local LLM provider."""

    name = "ollama"

    def __init__(
        self,
        base_url: str = OLLAMA_DEFAULT_BASE_URL,
        default_model: str = "gemma3:4b",
        timeout_seconds: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text using Ollama chat API."""
        model = request.model or self._default_model
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload: dict[str, object] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": request.max_tokens,
                "temperature": request.temperature,
            },
        }

        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            message = data.get("message", {})
            text = message.get("content", "")
            total_duration = data.get("total_duration", 0)
            eval_count = data.get("eval_count", 0)

            return AIResponse(
                text=text,
                model=model,
                provider="ollama",
                tokens_used=eval_count,
                finish_reason="stop",
                metadata={
                    "total_duration_ns": total_duration,
                    "eval_count": eval_count,
                },
            )
        except httpx.HTTPStatusError as exc:
            logger.error("Ollama error: %s", exc.response.status_code)
            raise
        except httpx.ConnectError:
            logger.error(
                "Cannot connect to Ollama at %s — is it running?",
                self._base_url,
            )
            raise

    async def health_check(self) -> bool:
        """Check if Ollama is running and responsive."""
        try:
            response = await self._client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models]
        except Exception:
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
