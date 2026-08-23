"""The ``genomeai-reference`` connector (deterministic mock source)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from genomeai_api.integration.connectors.base import (
    ConnectorHealth,
    DataSourceConfig,
    DataSourceConnector,
    DataSourceDefinition,
)
from genomeai_api.integration.connectors.fetcher import FetchRequest, HttpFetcher
from genomeai_api.integration.errors import IntegrationConfigurationError, NormalizationError
from genomeai_api.integration.types import AccessMode, AuthMode, SourceType


@dataclass(frozen=True)
class ReferenceFetchRequest:
    """Typed request for one page of reference records."""

    page: int = 1
    page_size: int = 10

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")


@dataclass(frozen=True)
class ReferenceRecord:
    """Typed record served by the reference mock source."""

    record_id: str
    symbol: str
    name: str
    source_version: str | None = None


@dataclass(frozen=True)
class ReferenceFetchResponse:
    """Typed fetch result for the reference source."""

    records: tuple[ReferenceRecord, ...]
    total: int
    page: int
    page_size: int
    source_version: str | None = None


def _required_str(item: dict[str, object], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise NormalizationError(
            f"Reference record field '{key}' must be a non-empty string",
        )
    return value


def _optional_str(item: dict[str, object], key: str) -> str | None:
    value = item.get(key)
    return value if isinstance(value, str) else None


class ReferenceConnector(DataSourceConnector):
    """Thin typed wrapper around the reference HTTP boundary."""

    definition = DataSourceDefinition(
        source_id="genomeai-reference",
        provider="GenomeAI",
        display_name="GenomeAI Reference Source",
        source_type=SourceType.OTHER,
        access_mode=AccessMode.LIVE,
        authentication_mode=AuthMode.NONE,
        license_info={"access": "reference-only", "redistribution": "connector-supplied"},
        description=(
            "Deterministic metadata-only reference source used to validate "
            "the Data Integration Foundation."
        ),
    )

    def __init__(self, config: DataSourceConfig, *, fetcher: HttpFetcher | None) -> None:
        super().__init__(config)
        if fetcher is None:
            raise IntegrationConfigurationError(
                f"Connector '{config.source_id}' requires an injected allowlisted fetcher"
            )
        self._fetcher = fetcher
        self._reported_version: str | None = None

    @property
    def current_version(self) -> str | None:
        return self._reported_version

    async def health_check(self) -> ConnectorHealth:
        result = await self._fetcher.fetch(FetchRequest(path="/reference/health"))
        payload = _payload_object(result.payload) or {}
        version = _optional_str(payload, "source_version")
        if version is not None:
            self._reported_version = version
        ok = payload.get("ok", False)
        message = _optional_str(payload, "message") or ""
        return ConnectorHealth(source_id=self.config.source_id, ok=bool(ok), message=message)

    async def fetch(self, request: object) -> ReferenceFetchResponse:
        if not isinstance(request, ReferenceFetchRequest):
            raise TypeError(
                f"ReferenceConnector.fetch expects ReferenceFetchRequest, "
                f"got {type(request).__name__}"
            )
        result = await self._fetcher.fetch(
            FetchRequest(
                path="/reference/records",
                params={"page": request.page, "page_size": request.page_size},
            )
        )
        return _parse_reference_payload(result.payload)


def _payload_object(payload: object) -> dict[str, object] | None:
    if isinstance(payload, dict):
        return cast(dict[str, object], payload)
    return None


def _parse_reference_payload(payload: object) -> ReferenceFetchResponse:
    """Parses and validates the reference payload shape (typed boundary)."""
    data = _payload_object(payload)
    if data is None:
        raise NormalizationError("Reference source returned a non-object payload")

    records_raw = data.get("records")
    if not isinstance(records_raw, list):
        raise NormalizationError("Reference source payload is missing a 'records' list")

    records: list[ReferenceRecord] = []
    for item in cast(list[object], records_raw):
        record_map = _payload_object(item)
        if record_map is None:
            raise NormalizationError("Reference record is not an object")
        try:
            records.append(
                ReferenceRecord(
                    record_id=_required_str(record_map, "record_id"),
                    symbol=_required_str(record_map, "symbol"),
                    name=_required_str(record_map, "name"),
                    source_version=_optional_str(record_map, "source_version"),
                )
            )
        except KeyError as exc:  # pragma: no cover - guarded by _required_str
            raise NormalizationError(
                f"Reference record is missing required field '{exc.args[0]}'",
            ) from exc

    total = data.get("total")
    page = data.get("page")
    page_size = data.get("page_size")

    return ReferenceFetchResponse(
        records=tuple(records),
        total=total if isinstance(total, int) else len(records),
        page=page if isinstance(page, int) else 1,
        page_size=page_size if isinstance(page_size, int) else len(records) or 1,
        source_version=_optional_str(data, "source_version"),
    )


def build_reference_connector(
    config: DataSourceConfig, *, fetcher: HttpFetcher
) -> ReferenceConnector:
    """Factory used by the :class:`SourceRegistry`."""
    return ReferenceConnector(config, fetcher=fetcher)
