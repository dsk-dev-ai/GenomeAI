from __future__ import annotations

import httpx
import pytest
from genomeai_api.integration.connectors.base import DataSourceConfig
from genomeai_api.integration.connectors.fetcher import HttpFetcher
from genomeai_api.integration.connectors.reference import (
    ReferenceConnector,
    ReferenceFetchRequest,
)
from genomeai_api.integration.connectors.reference.connector import (
    ReferenceFetchResponse,
)
from genomeai_api.integration.errors import IntegrationConfigurationError, NormalizationError

BASE = "https://reference.internal"


def _fetcher(handler) -> HttpFetcher:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return HttpFetcher(BASE, allowed_source_urls=[BASE], client=client)


def _connector(fetcher: HttpFetcher) -> ReferenceConnector:
    config = DataSourceConfig(source_id="genomeai-reference", api_base_url=BASE)
    return ReferenceConnector(config, fetcher=fetcher)


HEALTH_PAYLOAD = {
    "ok": True,
    "message": "reference source healthy",
    "source_version": "2026.08",
}

RECORDS_PAYLOAD = {
    "source_version": "2026.08",
    "total": 2,
    "page": 1,
    "page_size": 10,
    "records": [
        {"record_id": "REF:1", "symbol": "TP53", "name": "Tumor protein p53"},
        {"record_id": "REF:2", "symbol": "BRCA1", "name": "BRCA DNA repair"},
    ],
}


@pytest.mark.asyncio
async def test_health_check_reports_ok_and_version() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/reference/health"
        return httpx.Response(200, json=HEALTH_PAYLOAD)

    fetcher = _fetcher(handler)
    try:
        connector = _connector(fetcher)
        health = await connector.health_check()
        assert health.ok is True
        assert health.source_id == "genomeai-reference"
        assert connector.current_version == "2026.08"
    finally:
        await fetcher.aclose()


@pytest.mark.asyncio
async def test_health_check_reports_unhealthy_source() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "message": "degraded"})

    fetcher = _fetcher(handler)
    try:
        connector = _connector(fetcher)
        health = await connector.health_check()
        assert health.ok is False
        assert health.message == "degraded"
    finally:
        await fetcher.aclose()


@pytest.mark.asyncio
async def test_fetch_returns_typed_response() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["page"] = request.url.params["page"]
        seen["page_size"] = request.url.params["page_size"]
        return httpx.Response(200, json=RECORDS_PAYLOAD)

    fetcher = _fetcher(handler)
    try:
        connector = _connector(fetcher)
        result = await connector.fetch(ReferenceFetchRequest(page=3, page_size=25))
    finally:
        await fetcher.aclose()

    assert isinstance(result, ReferenceFetchResponse)
    assert seen == {"path": "/reference/records", "page": "3", "page_size": "25"}
    assert len(result.records) == 2
    assert result.records[0].record_id == "REF:1"
    assert result.total == 2


@pytest.mark.asyncio
async def test_fetch_rejects_wrong_request_type() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        return httpx.Response(200)

    fetcher = _fetcher(handler)
    try:
        connector = _connector(fetcher)
        with pytest.raises(TypeError, match="ReferenceFetchRequest"):
            await connector.fetch({"page": 1})
    finally:
        await fetcher.aclose()


@pytest.mark.asyncio
async def test_fetch_rejects_malformed_payloads() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"nope": True})

    fetcher = _fetcher(handler)
    try:
        connector = _connector(fetcher)
        with pytest.raises(NormalizationError):
            await connector.fetch(ReferenceFetchRequest())
    finally:
        await fetcher.aclose()


def test_disabled_source_cannot_build_connector() -> None:
    config = DataSourceConfig(
        source_id="genomeai-reference", api_base_url=BASE, enabled=False
    )
    with pytest.raises(IntegrationConfigurationError, match="disabled"):
        ReferenceConnector(config, fetcher=None)


@pytest.mark.parametrize("bad", [{"page": 0}, {"page": 1, "page_size": 0}, {"page": -1}])
def test_reference_request_validation(bad: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        ReferenceFetchRequest(**bad)
