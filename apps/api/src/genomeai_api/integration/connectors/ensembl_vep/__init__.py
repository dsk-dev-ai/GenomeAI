"""Ensembl VEP connector — variant effect predictions."""

from genomeai_api.integration.connectors.ensembl_vep.client import EnsemblVEPClient
from genomeai_api.integration.connectors.ensembl_vep.models import VEPResult

__all__ = ["EnsemblVEPClient", "VEPResult"]
