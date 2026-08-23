"""Data-source registry.

Maps stable source IDs to connector factories so services never hard-code
provider knowledge. The registry holds *definitions* (static metadata) and
*factories* (how to build a bound connector); it performs no I/O itself.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from genomeai_api.integration.connectors.base import (
    DataSourceConfig,
    DataSourceConnector,
    DataSourceDefinition,
)
from genomeai_api.integration.errors import ConnectorNotFoundError

ConnectorFactory = Callable[..., DataSourceConnector]


@dataclass(frozen=True)
class RegisteredSource:
    definition: DataSourceDefinition
    factory: ConnectorFactory


class SourceRegistry:
    """In-memory registry of known external sources."""

    def __init__(self) -> None:
        self._sources: dict[str, RegisteredSource] = {}

    def register(
        self, definition: DataSourceDefinition, factory: ConnectorFactory
    ) -> None:
        if definition.source_id in self._sources:
            raise ValueError(f"Data source '{definition.source_id}' already registered")
        self._sources[definition.source_id] = RegisteredSource(
            definition=definition, factory=factory
        )

    def has(self, source_id: str) -> bool:
        return source_id in self._sources

    def definition(self, source_id: str) -> DataSourceDefinition:
        try:
            return self._sources[source_id].definition
        except KeyError:
            raise ConnectorNotFoundError(
                f"No connector registered for source '{source_id}'"
            ) from None

    def factory(self, source_id: str) -> ConnectorFactory:
        try:
            return self._sources[source_id].factory
        except KeyError:
            raise ConnectorNotFoundError(
                f"No connector registered for source '{source_id}'"
            ) from None

    def build_connector(
        self, source_id: str, config: DataSourceConfig, **kwargs: object
    ) -> DataSourceConnector:
        """Builds a connector via its factory.

        Extra keyword arguments (e.g. an injected ``fetcher``) are forwarded to
        the factory so the registry stays I/O-agnostic.
        """
        if config.source_id != source_id:
            raise ValueError(
                f"Config source id '{config.source_id}' does not match '{source_id}'"
            )
        return self.factory(source_id)(config, **kwargs)

    def list_definitions(self) -> list[DataSourceDefinition]:
        return [entry.definition for entry in self._sources.values()]
