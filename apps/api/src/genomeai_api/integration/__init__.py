"""Data Integration Foundation (reusable external-source architecture).

Public boundary: types, errors, connector contracts, registry, and the raw /
normalized / identifier / provenance / job models that future Phase 7
ingestions build upon.
"""

from genomeai_api.integration.errors import (
    ConnectorNotFoundError,
    DataSourceNotFoundError,
    FetcherError,
    FetcherTransportError,
    FetchTimeoutError,
    IncompatibleConnectorError,
    IntegrationConfigurationError,
    IntegrationError,
    InvalidJobTransitionError,
    NormalizationError,
    UnsafeSourceUrlError,
)
from genomeai_api.integration.identifiers import ExternalIdentifier
from genomeai_api.integration.jobs import IngestionJob
from genomeai_api.integration.raw_data import (
    ProvenanceRecord,
    RawRecord,
    checksum_bytes,
    checksum_json,
)
from genomeai_api.integration.registry import SourceRegistry
from genomeai_api.integration.types import (
    AccessMode,
    AuthMode,
    EntityType,
    JobState,
    SourceType,
    SyncStatus,
)

__all__ = [
    "AccessMode",
    "AuthMode",
    "ConnectorNotFoundError",
    "DataSourceNotFoundError",
    "EntityType",
    "ExternalIdentifier",
    "FetchTimeoutError",
    "FetcherError",
    "FetcherTransportError",
    "IncompatibleConnectorError",
    "IngestionJob",
    "IntegrationConfigurationError",
    "IntegrationError",
    "InvalidJobTransitionError",
    "JobState",
    "NormalizationError",
    "ProvenanceRecord",
    "RawRecord",
    "SourceRegistry",
    "SourceType",
    "SyncStatus",
    "UnsafeSourceUrlError",
    "checksum_bytes",
    "checksum_json",
]
