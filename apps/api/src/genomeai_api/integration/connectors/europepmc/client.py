"""Europe PMC connector — biomedical literature search."""

from __future__ import annotations

import logging

import httpx

from genomeai_api.integration.connectors.europepmc.models import EuropePMCArticle

logger = logging.getLogger(__name__)

EUROPEPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"


class EuropePMCClient:
    """Async Europe PMC REST client."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=EUROPEPMC_API_URL,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[EuropePMCArticle]:
        """Search Europe PMC for articles."""
        params: dict[str, str | int] = {
            "query": query,
            "format": "json",
            "pageSize": max_results,
            "resultType": "core",
        }
        try:
            response = await self._client.get("/search", params=params)
            response.raise_for_status()
            data: dict[str, object] = response.json()
            results_raw = data.get("resultList", {})
            results_dict: dict[str, object] = (
                results_raw if isinstance(results_raw, dict) else {}
            )
            results_list = results_dict.get("result", [])
            articles: list[EuropePMCArticle] = []
            if isinstance(results_list, list):
                for r in results_list:
                    r_dict: dict[str, object] = r if isinstance(r, dict) else {}
                    if r_dict:
                        articles.append(self._parse_article(r_dict))
            return articles
        except httpx.HTTPStatusError as exc:
            logger.warning("Europe PMC search error: %s", exc.response.status_code)
            return []

    async def get_article(self, pmid: str) -> EuropePMCArticle | None:
        """Fetch a single article by PMID."""
        params: dict[str, str | int] = {
            "query": f"EXT_ID:{pmid}",
            "format": "json",
            "resultType": "core",
        }
        try:
            response = await self._client.get("/search", params=params)
            response.raise_for_status()
            data: dict[str, object] = response.json()
            results_raw = data.get("resultList", {})
            results_dict: dict[str, object] = (
                results_raw if isinstance(results_raw, dict) else {}
            )
            results_list = results_dict.get("result", [])
            if isinstance(results_list, list) and results_list:
                first = results_list[0]
                first_dict: dict[str, object] = (
                    first if isinstance(first, dict) else {}
                )
                if first_dict:
                    return self._parse_article(first_dict)
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning("Europe PMC fetch error: %s", exc.response.status_code)
            return None

    def _parse_article(self, data: dict[str, object]) -> EuropePMCArticle:
        pmid_raw = data.get("pmid", "")
        pmid = str(pmid_raw) if isinstance(pmid_raw, str) else ""
        pmcid_raw = data.get("pmcid", "")
        pmcid = str(pmcid_raw) if isinstance(pmcid_raw, str) else ""
        title_raw = data.get("title", "")
        title = str(title_raw) if isinstance(title_raw, str) else ""
        journal_raw = data.get("journalTitle", "")
        journal = str(journal_raw) if isinstance(journal_raw, str) else ""
        pub_date_raw = data.get("firstPublicationDate", "")
        pub_date = str(pub_date_raw) if isinstance(pub_date_raw, str) else ""
        abstract_raw = data.get("abstractText", "")
        abstract = str(abstract_raw) if isinstance(abstract_raw, str) else ""
        doi_raw = data.get("doi", "")
        doi = str(doi_raw) if isinstance(doi_raw, str) else ""
        cited_raw = data.get("citedByCount", 0)
        cited = int(cited_raw) if isinstance(cited_raw, (int, float)) else 0
        oa_raw = data.get("isOpenAccess", "")
        open_access = str(oa_raw) == "Y"

        raw_authors = data.get("authorString", "")
        author_str = str(raw_authors) if isinstance(raw_authors, str) else ""
        authors = [a.strip() for a in author_str.split(",") if a.strip()]

        raw_kw = data.get("keywordList", {})
        kw_dict: dict[str, object] = (
            raw_kw if isinstance(raw_kw, dict) else {}
        )
        kw_inner = kw_dict.get("keyword", [])
        keywords: list[str] = []
        if isinstance(kw_inner, list):
            for k in kw_inner:
                if isinstance(k, str):
                    keywords.append(k)

        return EuropePMCArticle(
            pmid=pmid,
            pmcid=pmcid,
            title=title,
            authors=authors,
            journal=journal,
            pub_date=pub_date,
            abstract=abstract,
            doi=doi,
            cited_by_count=cited,
            keywords=keywords,
            open_access=open_access,
        )

    async def health_check(self) -> bool:
        try:
            params: dict[str, str | int] = {
                "query": "BRCA1",
                "format": "json",
                "pageSize": 1,
            }
            response = await self._client.get("/search", params=params)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()
