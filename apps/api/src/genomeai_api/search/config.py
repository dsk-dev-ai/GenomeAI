from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class BackendConfig:
    backend: str = field(default_factory=lambda: os.getenv("SEARCH_BACKEND", "postgres"))
    url: str | None = field(default_factory=lambda: os.getenv("SEARCH_URL"))
    username: str | None = field(default_factory=lambda: os.getenv("SEARCH_USERNAME"))
    password: str | None = field(default_factory=lambda: os.getenv("SEARCH_PASSWORD"))
    index_prefix: str = field(
        default_factory=lambda: os.getenv("SEARCH_INDEX_PREFIX", "genomeai")
    )

    @property
    def is_opensearch(self) -> bool:
        return self.backend == "opensearch"

    @property
    def is_elasticsearch(self) -> bool:
        return self.backend == "elasticsearch"

    @property
    def is_postgres(self) -> bool:
        return self.backend == "postgres"


def load_backend_config() -> BackendConfig:
    return BackendConfig()
