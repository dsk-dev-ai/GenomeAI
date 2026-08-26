"""gnomAD connector — population variant frequencies via GraphQL."""

from genomeai_api.integration.connectors.gnomad.client import GnomADClient
from genomeai_api.integration.connectors.gnomad.models import GnomADVariant

__all__ = ["GnomADClient", "GnomADVariant"]
