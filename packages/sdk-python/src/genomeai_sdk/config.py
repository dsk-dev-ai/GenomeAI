from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SDKConfig:
    base_url: str = "http://localhost:8000"
    api_key: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    user_agent: str = field(default_factory=lambda: "genomeai-sdk/0.1.0")
