"""PDB connector — protein 3D structures via RCSB Data API."""

from genomeai_api.integration.connectors.pdb.client import PDBClient
from genomeai_api.integration.connectors.pdb.models import PDBStructure

__all__ = ["PDBClient", "PDBStructure"]
