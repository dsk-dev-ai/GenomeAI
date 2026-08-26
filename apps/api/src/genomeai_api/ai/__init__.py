"""AI module — multi-provider LLM gateway for genomic analysis.

Provides a unified interface to talk to any LLM provider.
V1: Ollama (local, free, unlimited)
V2: Gemini, OpenRouter, Groq, Mistral (free tiers)
"""

from genomeai_api.ai.base import AIProvider, AIRequest, AIResponse
from genomeai_api.ai.ollama import OllamaProvider

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "OllamaProvider",
]
