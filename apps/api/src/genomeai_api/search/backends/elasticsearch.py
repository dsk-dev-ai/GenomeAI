from __future__ import annotations

import asyncio
from typing import Any

from genomeai_api.search.backends._base import BaseSearchEngineBackend


class ElasticsearchBackend(BaseSearchEngineBackend):
    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from elasticsearch import Elasticsearch  # type: ignore[import-untyped]

            kwargs: dict[str, Any] = {"hosts": self._hosts}
            if self._username and self._password:
                kwargs["basic_auth"] = (self._username, self._password)
            self._client = Elasticsearch(**kwargs)
            return self._client
        except ImportError:
            msg = "elasticsearch is not installed. Install with: pip install elasticsearch"
            raise ImportError(msg)

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            return await asyncio.to_thread(client.ping)
        except Exception:
            return False
