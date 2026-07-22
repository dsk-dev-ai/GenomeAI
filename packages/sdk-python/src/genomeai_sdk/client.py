from __future__ import annotations

from typing import Any

import httpx

from genomeai_sdk.configuration import Configuration
from genomeai_sdk.exceptions import APIError, ConnectionError, TimeoutError


class Client:
    def __init__(self, configuration: Configuration | None = None) -> None:
        self.config = configuration or Configuration()
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.extra_headers)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise TimeoutError(str(exc)) from exc
        except httpx.ConnectError as exc:
            raise ConnectionError(str(exc)) from exc

        if response.is_error:
            raise APIError(response.status_code, response.text)

        return response

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("POST", path, **kwargs)

    async def health(self) -> dict[str, Any]:
        response = await self.get("/health")
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
