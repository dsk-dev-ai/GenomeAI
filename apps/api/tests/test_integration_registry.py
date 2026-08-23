from __future__ import annotations

import pytest
from genomeai_api.integration.connectors.base import DataSourceConfig, DataSourceDefinition
from genomeai_api.integration.errors import ConnectorNotFoundError
from genomeai_api.integration.registry import SourceRegistry
from genomeai_api.integration.types import SourceType


def _definition(source_id: str = "src-a") -> DataSourceDefinition:
    return DataSourceDefinition(
        source_id=source_id,
        provider="Provider",
        display_name="Source A",
        source_type=SourceType.OTHER,
    )


def _factory(config: DataSourceConfig) -> str:
    return f"connector:{config.source_id}"


def test_register_and_lookup() -> None:
    registry = SourceRegistry()
    registry.register(_definition(), _factory)

    assert registry.has("src-a")
    assert registry.definition("src-a").display_name == "Source A"
    connector = registry.build_connector("src-a", DataSourceConfig(source_id="src-a", api_base_url="https://example.com"))
    assert connector == "connector:src-a"


def test_duplicate_registration_rejected() -> None:
    registry = SourceRegistry()
    registry.register(_definition(), _factory)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(_definition(), _factory)


def test_unknown_source_raises_connector_not_found() -> None:
    registry = SourceRegistry()
    with pytest.raises(ConnectorNotFoundError):
        registry.definition("missing")
    with pytest.raises(ConnectorNotFoundError):
        registry.factory("missing")


def test_build_connector_rejects_mismatched_config() -> None:
    registry = SourceRegistry()
    registry.register(_definition(), _factory)
    config = DataSourceConfig(source_id="other", api_base_url="https://example.com")
    with pytest.raises(ValueError, match="does not match"):
        registry.build_connector("src-a", config)


def test_list_definitions_round_trip() -> None:
    registry = SourceRegistry()
    registry.register(_definition("a"), _factory)
    registry.register(_definition("b"), _factory)
    ids = [d.source_id for d in registry.list_definitions()]
    assert ids == ["a", "b"]
