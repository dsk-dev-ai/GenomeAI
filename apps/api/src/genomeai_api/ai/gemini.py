"""Google Gemini AI provider - free tier, fast inference.

Uses google-genai SDK with Gemini Flash models (free tier: 0 cost, generous RPM).
Requires GEMINI_API_KEY or GOOGLE_API_KEY env var.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Awaitable
from typing import Any, cast

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIProvider):
    """Google Gemini AI provider (free tier)."""

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str | None = None,
    ) -> None:
        # Google documents GOOGLE_API_KEY as taking precedence when both are set.
        self._api_key = (
            api_key
            if api_key is not None
            else os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GEMINI_API_KEY", "")
        )
        self._default_model = (
            default_model
            or os.environ.get("GENOMEAI_GEMINI_MODEL")
            or os.environ.get("GEMINI_MODEL")
            or DEFAULT_GEMINI_MODEL
        )
        self._client: Any = None

    def _get_client(self) -> Any:
        if not self._api_key:
            raise RuntimeError(
                "Gemini API key is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY."
            )
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def generate(self, request: AIRequest) -> AIResponse:
        model = request.model or self._default_model
        client = self._get_client()

        system_instruction = request.system_prompt or None
        contents = request.prompt

        try:
            config: dict[str, Any] = {
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
                config=config,
            )

            text = str(response.text) if response.text else ""
            metadata: dict[str, Any] = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                meta = response.usage_metadata
                metadata["prompt_tokens"] = int(
                    getattr(meta, "prompt_token_count", 0) or 0
                )
                metadata["completion_tokens"] = int(
                    getattr(meta, "candidates_token_count", 0) or 0
                )
                metadata["total_tokens"] = int(
                    getattr(meta, "total_token_count", 0) or 0
                )

            return AIResponse(
                text=text,
                model=model,
                provider="gemini",
                tokens_used=int(metadata.get("total_tokens", 0)),
                finish_reason="stop",
                metadata=metadata,
            )
        except Exception as exc:
            logger.error("Gemini error: %s", exc)
            raise

    async def health_check(self) -> bool:
        try:
            if not self._api_key:
                return False
            client = self._get_client()
            await asyncio.to_thread(
                client.models.generate_content,
                model=self._default_model,
                contents="Hi",
                config={"max_output_tokens": 5},
            )
            return True
        except Exception as exc:
            logger.warning("Gemini health check failed: %s", exc)
            return False

    async def list_models(self) -> list[str]:
        try:
            client = self._get_client()
            models = await asyncio.to_thread(client.models.list)
            return [str(m.name) for m in models if hasattr(m, "name")]
        except Exception:
            return []

    async def close(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return

        try:
            close = getattr(client, "close", None)
            if callable(close):
                close()
        except AttributeError as exc:
            if "_async_httpx_client" not in str(exc):
                raise
            logger.debug("Ignoring google-genai sync close noise: %s", exc)

        try:
            aio = getattr(client, "aio", None)
            aclose = getattr(aio, "aclose", None)
            if aclose is not None:
                await cast("Awaitable[Any]", aclose())
        except AttributeError as exc:
            if "_async_httpx_client" not in str(exc):
                raise
            logger.debug("Ignoring google-genai async close noise: %s", exc)
