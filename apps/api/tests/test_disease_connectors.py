"""Real API tests for disease analysis connectors (OpenTargets, Disease Ontology, Monarch)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import pytest
from genomeai_api.integration.connectors.disease_ontology import DiseaseOntologyClient
from genomeai_api.integration.connectors.monarch import MonarchClient
from genomeai_api.integration.connectors.opentargets import OpenTargetsClient


def retry_transient(retries: int = 3, delay: float = 3.0) -> Callable[..., Any]:
    """Decorator: retry on transient network/server errors, then skip on outage.

    After retries are exhausted for a purely-transient/service-unavailable
    failure, the test is skipped rather than failing CI — matching the
    connector-test flake handling (PR #62).
    """

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
            pytest.skip(f"External API unavailable after {retries} retries: {last_exc}")

        return wrapper

    return decorator


@pytest.mark.asyncio
class TestOpenTargets:
    @retry_transient()
    async def test_search_disease(self) -> None:
        client = OpenTargetsClient()
        try:
            results = await client.search_disease("breast cancer", size=3)
            assert len(results) >= 1
            assert results[0].get("name", "") != ""
            assert results[0].get("id", "") != ""
            print(f"  OpenTargets breast cancer: {len(results)} results")
            print(f"  First: {results[0].get('name')} [{results[0].get('id')}]")
        finally:
            await client.close()

    @retry_transient()
    async def test_resolve_gene(self) -> None:
        client = OpenTargetsClient()
        try:
            ensembl_id = await client.resolve_gene_to_ensembl("BRCA1")
            assert ensembl_id is not None
            assert ensembl_id.startswith("ENSG")
            print(f"  OpenTargets BRCA1 -> {ensembl_id}")
        finally:
            await client.close()

    @retry_transient()
    async def test_get_target_diseases(self) -> None:
        client = OpenTargetsClient()
        try:
            ensembl_id = await client.resolve_gene_to_ensembl("BRCA1")
            assert ensembl_id is not None
            data = await client.get_target_diseases(ensembl_id, size=3)
            assert "associatedDiseases" in data
            assocs = data.get("associatedDiseases", {})
            if isinstance(assocs, dict):
                rows = assocs.get("rows", [])
                assert isinstance(rows, list)
                assert len(rows) >= 1
                print(f"  OpenTargets BRCA1 diseases: {len(rows)}")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = OpenTargetsClient()
        try:
            health = await client.health_check()
        finally:
            await client.close()
        if not health:
            pytest.skip("OpenTargets API unavailable")


@pytest.mark.asyncio
class TestDiseaseOntology:
    @retry_transient()
    async def test_get_term(self) -> None:
        client = DiseaseOntologyClient()
        try:
            term = await client.get_term("DOID:9970")
            assert term is not None
            assert term.get("id") == "DOID:9970"
            assert term.get("name", "") != ""
            assert term.get("definition", "") != ""
            print(f"  DO term: {term.get('name')} [{term.get('id')}]")
        finally:
            await client.close()

    @retry_transient()
    async def test_search_terms(self) -> None:
        client = DiseaseOntologyClient()
        try:
            results = await client.search_terms("breast cancer")
            assert len(results) >= 1
            assert results[0].get("name", "") != ""
            print(f"  DO search: {len(results)} results")
            print(f"  First: {results[0].get('name')} [{results[0].get('id')}]")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = DiseaseOntologyClient()
        try:
            health = await client.health_check()
        finally:
            await client.close()
        if not health:
            pytest.skip("Disease Ontology API unavailable")


@pytest.mark.asyncio
class TestMonarch:
    @retry_transient()
    async def test_search(self) -> None:
        client = MonarchClient()
        try:
            results = await client.search("marfan syndrome", limit=3)
            assert len(results) >= 1
            assert results[0].get("name", results[0].get("label", "")) != ""
            assert results[0].get("id", "") != ""
            print(f"  Monarch marfan: {len(results)} results")
            first_name = results[0].get("name", results[0].get("label", ""))
            first_id = results[0].get("id", "")
            print(f"  First: {first_name} [{first_id}]")
        finally:
            await client.close()

    async def test_health_check(self) -> None:
        client = MonarchClient()
        try:
            health = await client.health_check()
        finally:
            await client.close()
        if not health:
            pytest.skip("Monarch API unavailable")
