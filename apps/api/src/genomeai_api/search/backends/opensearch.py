from __future__ import annotations

import asyncio
from typing import Any

from genomeai_api.search.backends._base import BaseSearchEngineBackend


class OpenSearchBackend(BaseSearchEngineBackend):
    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from opensearchpy import OpenSearch  # type: ignore[import-untyped]

            kwargs: dict[str, Any] = {"hosts": self._hosts}
            if self._username and self._password:
                kwargs["http_auth"] = (self._username, self._password)
            self._client = OpenSearch(**kwargs)
            return self._client
        except ImportError:
            msg = "opensearch-py is not installed. Install with: pip install opensearch-py"
            raise ImportError(msg)

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            info = await asyncio.to_thread(client.info)
            return info.get("status", 0) == 200 or "cluster_name" in info
        except Exception:
            return False
