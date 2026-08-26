"""Semantic Scholar connector — academic paper search."""

from genomeai_api.integration.connectors.semanticscholar.client import SemanticScholarClient
from genomeai_api.integration.connectors.semanticscholar.models import SemanticScholarPaper

__all__ = ["SemanticScholarClient", "SemanticScholarPaper"]
