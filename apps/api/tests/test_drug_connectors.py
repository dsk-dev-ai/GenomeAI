"""Real API tests for drug search connectors (ChEMBL + PubChem)."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any

import pytest
from genomeai_api.integration.connectors.chembl.client import ChEMBLClient
from genomeai_api.integration.connectors.pubchem.client import PubChemClient


def _retry_transient(retries: int = 3, delay: float = 3.0) -> Callable[..., Any]:
    """Decorator: retry an async function on transient network/server errors."""

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
class TestChEMBL:
    @_retry_transient()
    async def test_search_aspirin(self) -> None:
        client = ChEMBLClient()
        try:
            drugs = await client.search_drugs("aspirin", max_results=3)
            assert len(drugs) >= 1
            assert drugs[0].name != ""
            print(f"  ChEMBL aspirin: {len(drugs)} drugs")
            print(f"  First: {drugs[0].name}")
        finally:
            await client.close()

    @_retry_transient()
    async def test_get_drug(self) -> None:
        client = ChEMBLClient()
        try:
            drug = await client.get_drug("CHEMBL25")
            assert drug is not None
            assert drug.molecule_chembl_id == "CHEMBL25"
            print(f"  Drug: {drug.name} ({drug.molecule_chembl_id})")
        finally:
            await client.close()

    @_retry_transient()
    async def test_health(self) -> None:
        client = ChEMBLClient()
        try:
            ok = await client.health_check()
            if not ok:
                pytest.skip("ChEMBL API unavailable")
            assert ok
        finally:
            await client.close()


@pytest.mark.asyncio
class TestPubChem:
    @_retry_transient()
    async def test_search_aspirin(self) -> None:
        client = PubChemClient()
        try:
            compound = await client.search_by_name("aspirin")
            assert compound is not None
            assert compound.cid > 0
            assert compound.molecular_formula != ""
            print(f"  PubChem aspirin: CID {compound.cid}")
            print(f"  Formula: {compound.molecular_formula}")
            print(f"  MW: {compound.molecular_weight}")
        finally:
            await client.close()

    async def test_health(self) -> None:
        client = PubChemClient()
        try:
            assert await client.health_check()
        finally:
            await client.close()
