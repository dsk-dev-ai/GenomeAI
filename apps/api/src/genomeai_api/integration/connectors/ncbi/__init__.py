"""NCBI E-utilities connector — fetch genes, sequences, literature, variants.

Uses NCBI E-utilities REST API (free, no key required, 3 req/s).
Covers 38 biomedical databases via esearch, efetch, esummary, elink, einfo.
"""

from genomeai_api.integration.connectors.ncbi.client import NCBIClient
from genomeai_api.integration.connectors.ncbi.gene import NCBIGeneConnector
from genomeai_api.integration.connectors.ncbi.models import (
    NCBIGeneRecord,
    NCBISearchResult,
)

__all__ = [
    "NCBIGeneConnector",
    "NCBIClient",
    "NCBIGeneRecord",
    "NCBISearchResult",
]
