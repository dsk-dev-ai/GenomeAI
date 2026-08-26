"""AlphaFold connector — predicted protein structures from AlphaFold DB."""

from genomeai_api.integration.connectors.alphafold.client import AlphaFoldClient
from genomeai_api.integration.connectors.alphafold.models import AlphaFoldStructure

__all__ = ["AlphaFoldClient", "AlphaFoldStructure"]
