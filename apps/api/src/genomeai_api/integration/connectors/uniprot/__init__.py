"""UniProt connector — protein sequences, function, annotations."""

from genomeai_api.integration.connectors.uniprot.client import UniProtClient
from genomeai_api.integration.connectors.uniprot.models import UniProtProtein

__all__ = ["UniProtClient", "UniProtProtein"]
