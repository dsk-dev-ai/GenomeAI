"""Wires concrete connectors into a :class:`SourceRegistry`.

This is the single place where the application decides which connectors exist.
Future milestones add real providers here; nothing else changes.
"""

from __future__ import annotations

from genomeai_api.integration.connectors.base import DataSourceConfig
from genomeai_api.integration.connectors.fetcher import HttpFetcher
from genomeai_api.integration.connectors.reference import build_reference_connector
from genomeai_api.integration.errors import IntegrationConfigurationError
from genomeai_api.integration.registry import SourceRegistry


def _reference_factory(
    config: DataSourceConfig, *, fetcher: HttpFetcher | None
):
    if fetcher is None:
        raise IntegrationConfigurationError(
            "Reference connector requires an injected allowlisted fetcher"
        )
    return build_reference_connector(config, fetcher=fetcher)


def build_default_registry() -> SourceRegistry:
    """Registry containing every connector compiled into this service."""
    from genomeai_api.integration.connectors.reference.connector import (
        ReferenceConnector,
    )

    registry = SourceRegistry()
    registry.register(ReferenceConnector.definition, _reference_factory)
    return registry
