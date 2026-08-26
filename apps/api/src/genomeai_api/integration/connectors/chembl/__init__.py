"""ChEMBL connector — drug targets and bioactivity data."""

from genomeai_api.integration.connectors.chembl.client import ChEMBLClient
from genomeai_api.integration.connectors.chembl.models import ChEMBLBioactivity, ChEMBLDrug

__all__ = ["ChEMBLClient", "ChEMBLBioactivity", "ChEMBLDrug"]
