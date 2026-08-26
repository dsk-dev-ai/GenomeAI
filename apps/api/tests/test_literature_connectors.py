"""Real API tests for literature search connectors (Europe PMC + Semantic Scholar)."""

from __future__ import annotations

import pytest
from genomeai_api.integration.connectors.europepmc.client import EuropePMCClient
from genomeai_api.integration.connectors.semanticscholar.client import SemanticScholarClient


@pytest.mark.asyncio
class TestEuropePMC:
    async def test_search_brca1(self) -> None:
        client = EuropePMCClient()
        try:
            articles = await client.search("BRCA1", max_results=3)
            assert len(articles) >= 1
            assert articles[0].pmid != "" or articles[0].title != ""
            print(f"  Europe PMC BRCA1: {len(articles)} articles")
            print(f"  First: {articles[0].title[:80]}...")
        finally:
            await client.close()

    async def test_get_article(self) -> None:
        client = EuropePMCClient()
        try:
            article = await client.get_article("30356099")
            assert article is not None
            assert article.pmid == "30356099"
            print(f"  Article: {article.title[:80]}...")
        finally:
            await client.close()

    async def test_health(self) -> None:
        client = EuropePMCClient()
        try:
            assert await client.health_check()
        finally:
            await client.close()


@pytest.mark.asyncio
class TestSemanticScholar:
    async def test_get_paper(self) -> None:
        client = SemanticScholarClient()
        try:
            paper = await client.get_paper("DOI:10.1038/nature12373")
            assert paper is not None
            assert paper.title != ""
            assert paper.citation_count > 0
            print(f"  Paper: {paper.title[:80]}...")
            print(f"  Citations: {paper.citation_count}")
        finally:
            await client.close()

    async def test_health(self) -> None:
        client = SemanticScholarClient()
        try:
            assert await client.health_check()
        finally:
            await client.close()
