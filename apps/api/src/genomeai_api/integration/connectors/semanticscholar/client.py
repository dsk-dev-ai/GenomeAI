"""Semantic Scholar connector — academic paper search."""

from __future__ import annotations

import asyncio
import logging

import httpx

from genomeai_api.integration.connectors.semanticscholar.models import SemanticScholarPaper

logger = logging.getLogger(__name__)

SEMANTICSCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1"
SS_RATE_LIMIT_DELAY = 3.5  # SS free tier: ~1 req/3s, conservative


class SemanticScholarClient:
    """Async Semantic Scholar REST client with rate limiting."""

    _last_request_time: float = 0.0

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=SEMANTICSCHOLAR_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def _rate_limit(self) -> None:
        now = asyncio.get_running_loop().time()
        elapsed = now - SemanticScholarClient._last_request_time
        if elapsed < SS_RATE_LIMIT_DELAY:
            await asyncio.sleep(SS_RATE_LIMIT_DELAY - elapsed)
        SemanticScholarClient._last_request_time = asyncio.get_running_loop().time()

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[SemanticScholarPaper]:
        """Search requires API key. Use get_paper for individual lookups."""
        return []

    async def get_paper(self, paper_id: str) -> SemanticScholarPaper | None:
        fields = ",".join([
            "paperId", "title", "authors", "abstract", "year",
            "citationCount", "journal", "externalIds", "isOpenAccess",
            "fieldsOfStudy", "url",
        ])
        last_exc: Exception | None = None
        for attempt in range(3):
            await self._rate_limit()
            try:
                response = await self._client.get(
                    f"/paper/{paper_id}",
                    params={"fields": fields},
                )
                if response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning("SS 429, retry in %ds", wait)
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                data: dict[str, object] = response.json()
                return self._parse_paper(data)
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code == 404:
                    return None
                if exc.response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning("SS 429, retry in %ds", wait)
                    await asyncio.sleep(wait)
                    continue
                logger.warning("Semantic Scholar fetch error: %s", exc.response.status_code)
                return None
            except Exception as exc:
                last_exc = exc
                break
        logger.warning("Semantic Scholar fetch failed after retries: %s", last_exc)
        return None

    def _parse_paper(self, data: dict[str, object]) -> SemanticScholarPaper:
        paper_id_raw = data.get("paperId", "")
        paper_id = str(paper_id_raw) if isinstance(paper_id_raw, str) else ""
        title_raw = data.get("title", "")
        title = str(title_raw) if isinstance(title_raw, str) else ""
        abstract_raw = data.get("abstract", "")
        abstract = str(abstract_raw) if isinstance(abstract_raw, str) else ""
        year_raw = data.get("year", 0)
        year = int(year_raw) if isinstance(year_raw, (int, float)) else 0
        cite_raw = data.get("citationCount", 0)
        citation_count = int(cite_raw) if isinstance(cite_raw, (int, float)) else 0
        url_raw = data.get("url", "")
        url = str(url_raw) if isinstance(url_raw, str) else ""
        oa_raw = data.get("isOpenAccess", False)
        open_access = bool(oa_raw)

        raw_journal = data.get("journal", {})
        journal_dict: dict[str, object] = (
            raw_journal if isinstance(raw_journal, dict) else {}
        )
        journal_name_raw = journal_dict.get("name", "")
        journal = str(journal_name_raw) if isinstance(journal_name_raw, str) else ""

        raw_ext = data.get("externalIds", {})
        ext_dict: dict[str, object] = (
            raw_ext if isinstance(raw_ext, dict) else {}
        )
        doi_raw = ext_dict.get("DOI", "")
        doi = str(doi_raw) if isinstance(doi_raw, str) else ""
        pmid_raw = ext_dict.get("PubMed", "")
        pmid = str(pmid_raw) if isinstance(pmid_raw, str) else ""

        raw_authors = data.get("authors", [])
        authors: list[str] = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict):
                    name_raw = a.get("name", "")
                    name = str(name_raw) if isinstance(name_raw, str) else ""
                    if name:
                        authors.append(name)

        raw_fos = data.get("fieldsOfStudy", [])
        fields_of_study: list[str] = []
        if isinstance(raw_fos, list):
            for f in raw_fos:
                if isinstance(f, str):
                    fields_of_study.append(f)

        return SemanticScholarPaper(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            citation_count=citation_count,
            journal=journal,
            doi=doi,
            pmid=pmid,
            open_access=open_access,
            fields_of_study=fields_of_study,
            url=url,
        )

    async def health_check(self) -> bool:
        try:
            fields = "paperId,title"
            await self._rate_limit()
            response = await self._client.get(
                "/paper/DOI:10.1038/nature12373",
                params={"fields": fields},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
