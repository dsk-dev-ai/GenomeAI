from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Configuration:
    base_url: str = "http://localhost:8000"
    api_key: str | None = None
    timeout: float = 30.0
    retry_on_failure: bool = True
    max_retries: int = 3
    extra_headers: dict[str, str] = field(default_factory=dict)
