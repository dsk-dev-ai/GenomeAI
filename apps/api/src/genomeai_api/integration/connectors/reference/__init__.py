"""Reference connector: proves the integration architecture end to end.

The ``genomeai-reference`` source is a deterministic metadata-only mock served
by tests via ``httpx.MockTransport`` (or any tiny HTTP stub). It demonstrates
registration, typed fetch, health check, normalization, and provenance without
touching any real external API.
"""

from genomeai_api.integration.connectors.reference.connector import (
    ReferenceConnector,
    ReferenceFetchRequest,
    ReferenceFetchResponse,
    ReferenceRecord,
    build_reference_connector,
)
from genomeai_api.integration.connectors.reference.normalizer import (
    ReferenceRecordNormalizer,
)

__all__ = [
    "ReferenceConnector",
    "ReferenceFetchRequest",
    "ReferenceFetchResponse",
    "ReferenceRecord",
    "ReferenceRecordNormalizer",
    "build_reference_connector",
]
