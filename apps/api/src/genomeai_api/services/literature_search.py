"""Literature search engine — Europe PMC + Semantic Scholar + Gemini AI."""

from __future__ import annotations

import logging

from genomeai_api.ai.base import AIProvider, AIRequest
from genomeai_api.integration.connectors.europepmc.client import EuropePMCClient
from genomeai_api.integration.connectors.europepmc.models import EuropePMCArticle
from genomeai_api.integration.connectors.semanticscholar.client import SemanticScholarClient
from genomeai_api.integration.connectors.semanticscholar.models import SemanticScholarPaper

logger = logging.getLogger(__name__)

LITERATURE_SUMMARY_PROMPT = """\
You are a genomics literature analyst. Analyze the following papers and provide a \
structured summary.

For each paper, provide:
1. Relevance to genomics research
2. Key findings or claims
3. Methodology summary
4. Clinical or research significance

Papers:
{papers}

Respond in JSON format:
{{
  "papers": [
    {{
      "title": "...",
      "relevance": "...",
      "key_findings": "...",
      "methodology": "...",
      "significance": "..."
    }}
  ],
  "summary": "...",
  "research_gaps": "..."
}}
"""


class LiteratureSearchEngine:
    """Literature search engine combining Europe PMC + Semantic Scholar + AI."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self._epmc = EuropePMCClient()
        self._ss = SemanticScholarClient()
        self._ai = ai_provider

    async def search(self, query: str, max_results: int = 10) -> dict[str, object]:
        """Search both Europe PMC and Semantic Scholar, return merged results."""
        epmc_articles = await self._epmc.search(query, max_results=max_results)
        ss_papers = await self._ss.search(query, max_results=max_results)

        results: dict[str, object] = {
            "query": query,
            "europepmc_count": len(epmc_articles),
            "semanticscholar_count": len(ss_papers),
            "europepmc_articles": [
                self._article_to_dict(a) for a in epmc_articles
            ],
            "semanticscholar_papers": [
                self._paper_to_dict(p) for p in ss_papers
            ],
        }
        return results

    async def analyze(self, query: str, max_results: int = 5) -> dict[str, object]:
        """Search and analyze papers with AI."""
        search_results = await self.search(query, max_results=max_results)
        all_papers: list[str] = []
        raw_articles = search_results.get("europepmc_articles", [])
        if isinstance(raw_articles, list):
            for a in raw_articles:
                a_dict: dict[str, object] = a if isinstance(a, dict) else {}
                if a_dict:
                    all_papers.append(self._article_to_str(a_dict))
        raw_papers = search_results.get("semanticscholar_papers", [])
        if isinstance(raw_papers, list):
            for p in raw_papers:
                p_dict: dict[str, object] = p if isinstance(p, dict) else {}
                if p_dict:
                    all_papers.append(self._paper_to_str(p_dict))

        if not all_papers:
            return {"error": "No papers found", "analysis": None}

        papers_text = "\n\n".join(all_papers)
        prompt = LITERATURE_SUMMARY_PROMPT.format(papers=papers_text)
        ai_request = AIRequest(prompt=prompt)

        try:
            ai_response = await self._ai.generate(ai_request)
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            return {
                "query": query,
                "papers_count": len(all_papers),
                "ai_analysis": None,
                "error": str(exc),
            }

        return {
            "query": query,
            "papers_count": len(all_papers),
            "ai_analysis": ai_response.text,
        }

    def _article_to_dict(self, article: EuropePMCArticle) -> dict[str, object]:
        return {
            "pmid": article.pmid,
            "pmcid": article.pmcid,
            "title": article.title,
            "authors": article.authors,
            "journal": article.journal,
            "pub_date": article.pub_date,
            "abstract": article.abstract[:500] if article.abstract else "",
            "doi": article.doi,
            "cited_by_count": article.cited_by_count,
            "keywords": article.keywords,
            "open_access": article.open_access,
            "source": "europepmc",
        }

    def _paper_to_dict(self, paper: SemanticScholarPaper) -> dict[str, object]:
        return {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "authors": paper.authors,
            "abstract": paper.abstract[:500] if paper.abstract else "",
            "year": paper.year,
            "citation_count": paper.citation_count,
            "journal": paper.journal,
            "doi": paper.doi,
            "pmid": paper.pmid,
            "open_access": paper.open_access,
            "fields_of_study": paper.fields_of_study,
            "url": paper.url,
            "source": "semanticscholar",
        }

    def _article_to_str(self, article: dict[str, object]) -> str:
        title = str(article.get("title", ""))
        abstract = str(article.get("abstract", ""))
        raw_authors = article.get("authors", [])
        authors_list: list[str] = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, str):
                    authors_list.append(a)
        authors = ", ".join(authors_list)
        journal = str(article.get("journal", ""))
        return f"Title: {title}\nAuthors: {authors}\nJournal: {journal}\nAbstract: {abstract}"

    def _paper_to_str(self, paper: dict[str, object]) -> str:
        title = str(paper.get("title", ""))
        abstract = str(paper.get("abstract", ""))
        raw_authors = paper.get("authors", [])
        authors_list: list[str] = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, str):
                    authors_list.append(a)
        authors = ", ".join(authors_list)
        year = str(paper.get("year", ""))
        return f"Title: {title}\nAuthors: {authors}\nYear: {year}\nAbstract: {abstract}"

    async def close(self) -> None:
        await self._epmc.close()
        await self._ss.close()
