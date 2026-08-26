"""PubChem connector — compound data and drug information."""

from genomeai_api.integration.connectors.pubchem.client import PubChemClient
from genomeai_api.integration.connectors.pubchem.models import PubChemCompound

__all__ = ["PubChemClient", "PubChemCompound"]
