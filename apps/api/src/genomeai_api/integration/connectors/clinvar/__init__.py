"""ClinVar connector — clinical variant interpretations via NCBI E-utilities."""

from genomeai_api.integration.connectors.clinvar.client import ClinVarClient
from genomeai_api.integration.connectors.clinvar.models import ClinVarRecord

__all__ = ["ClinVarClient", "ClinVarRecord"]
