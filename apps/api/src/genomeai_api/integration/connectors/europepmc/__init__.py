"""Europe PMC connector — biomedical literature search."""

from genomeai_api.integration.connectors.europepmc.client import EuropePMCClient
from genomeai_api.integration.connectors.europepmc.models import EuropePMCArticle

__all__ = ["EuropePMCClient", "EuropePMCArticle"]
