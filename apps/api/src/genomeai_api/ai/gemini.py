"""Google Gemini AI provider — free tier, fast inference.

Uses google-genai SDK with Gemini Flash models (free tier: 0 cost, generous RPM).
Requires GEMINI_API_KEY env var.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Google Gemini AI provider (free tier)."""

    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gemini-3.6-flash",
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._default_model = default_model
        self._client: Any = None

    def _get_client(self) -> Any:
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

            response = client.models.generate_content(
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
            client.models.generate_content(
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
            models = client.models.list()
            return [str(m.name) for m in models if hasattr(m, "name")]
        except Exception:
            return []

    async def close(self) -> None:
        self._client = None
