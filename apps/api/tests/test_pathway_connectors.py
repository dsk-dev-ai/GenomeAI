"""Real API tests for pathway analysis connectors (Reactome, STRING, KEGG)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import pytest
from genomeai_api.integration.connectors.kegg.client import KEGGClient
from genomeai_api.integration.connectors.reactome.client import ReactomeClient
from genomeai_api.integration.connectors.string_db.client import StringDBClient


def _retry_transient(retries: int = 3, delay: float = 3.0) -> Callable[..., Any]:
    """Decorator: retry on transient network/server errors."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    msg = str(exc).lower()
                    transient = any(
                        kw in msg
                        for kw in ("timeout", "connection", "remote", "incomplete", "server error")
                    )
                    if transient:
                        last_exc = exc
                        if attempt < retries - 1:
                            await asyncio.sleep(delay * (attempt + 1))
                        continue
                    raise
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


@pytest.mark.asyncio
class TestReactome:
    @_retry_transient()
    async def test_search_pathways(self) -> None:
        client = ReactomeClient()
        try:
            result = await client.search_pathways("BRCA1", species="Homo sapiens", max_results=3)
            assert result.total_matches > 0
            assert len(result.pathways) >= 1
            pw = result.pathways[0]
            assert pw.st_id != ""
            assert pw.name != ""
            assert pw.name[0] != "<"  # no HTML tags
            print(f"  Reactome BRCA1: {result.total_matches} total")
            print(f"  Returned: {len(result.pathways)}")
            print(f"  First: {pw.name} [{pw.st_id}]")
        finally:
            await client.close()

    @_retry_transient()
    async def test_get_pathway_detail(self) -> None:
        client = ReactomeClient()
        try:
            result = await client.search_pathways("TP53", species="Homo sapiens", max_results=1)
            if result.pathways:
                detail = await client.get_pathway_detail(result.pathways[0].st_id)
                assert detail is not None
                assert isinstance(detail, dict)
                print(f"  Reactome detail: {result.pathways[0].name}")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = ReactomeClient()
        try:
            health = await client.health_check()
            assert health is True
        finally:
            await client.close()


@pytest.mark.asyncio
class TestSTRING:
    @_retry_transient()
    async def test_get_string_ids(self) -> None:
        client = StringDBClient()
        try:
            ids = await client.get_string_ids(["BRCA1"], species=9606)
            assert len(ids) >= 1
            assert ids[0].preferred_name == "BRCA1"
            assert ids[0].string_id != ""
            print(f"  STRING BRCA1: {ids[0].string_id}")
        finally:
            await client.close()

    @_retry_transient()
    async def test_get_network(self) -> None:
        client = StringDBClient()
        try:
            interactions = await client.get_network(
                ["BRCA1", "TP53"], species=9606, required_score=400,
            )
            assert len(interactions) >= 1
            assert interactions[0].score > 0
            print(f"  STRING network: {len(interactions)} interactions")
        finally:
            await client.close()

    @_retry_transient()
    async def test_get_enrichment(self) -> None:
        client = StringDBClient()
        try:
            enrichment = await client.get_enrichment(["BRCA1", "TP53"], species=9606)
            assert len(enrichment) >= 1
            assert enrichment[0].term != ""
            assert enrichment[0].p_value >= 0
            print(f"  STRING enrichment: {len(enrichment)} terms")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = StringDBClient()
        try:
            health = await client.health_check()
            assert health is True
        finally:
            await client.close()


@pytest.mark.asyncio
class TestKEGG:
    @_retry_transient()
    async def test_get_pathways_for_gene(self) -> None:
        client = KEGGClient()
        try:
            pathways = await client.get_pathways_for_gene("hsa:672")  # BRCA1
            assert len(pathways) >= 1
            assert pathways[0].pathway_id != ""
            print(f"  KEGG BRCA1 pathways: {len(pathways)}")
            print(f"  First: {pathways[0].pathway_id}")
        finally:
            await client.close()

    @_retry_transient()
    async def test_list_pathways(self) -> None:
        client = KEGGClient()
        try:
            pathways = await client.list_pathways()
            assert len(pathways) > 100
            assert pathways[0].name != ""
            print(f"  KEGG total pathways: {len(pathways)}")
        finally:
            await client.close()

    @_retry_transient()
    async def test_get_pathway_detail(self) -> None:
        client = KEGGClient()
        try:
            detail = await client.get_pathway_detail("hsa03440")  # Homologous recombination
            assert detail is not None
            assert detail.name != ""
            assert len(detail.classes) >= 1
            print(f"  KEGG detail: {detail.name}")
            print(f"  Classes: {detail.classes}")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = KEGGClient()
        try:
            health = await client.health_check()
            assert health is True
        finally:
            await client.close()
