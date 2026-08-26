"""Abstract AI provider interface.

Every AI provider (Ollama, Gemini, OpenRouter, etc.) implements this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AIRequest:
    """Request to an AI provider."""

    prompt: str
    model: str = ""
    system_prompt: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7


@dataclass
class AIResponse:
    """Response from an AI provider."""

    text: str
    model: str = ""
    provider: str = ""
    tokens_used: int = 0
    finish_reason: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base for AI providers."""

    name: str

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate text from a prompt."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models."""

    async def close(self) -> None:
        """Release resources."""
