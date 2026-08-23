from __future__ import annotations

import uuid

import pytest
from genomeai_api.integration.identifiers import ExternalIdentifier, ExternalIdentifierStore


class InMemoryIdentifierStore:
    """Fake implementing the ExternalIdentifierStore contract.

    Mirrors the database uniqueness rule: (source, external_id, entity_type)
    must be unique within each namespace scope.
    """

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str, str, str | None], ExternalIdentifier] = {}

    def create(self, identifier: ExternalIdentifier) -> ExternalIdentifier:
        key = (
            identifier.source,
            identifier.external_id,
            identifier.entity_type,
            identifier.namespace,
        )
        if key in self._rows:
            raise ValueError("duplicate external identifier")
        self._rows[key] = identifier
        return identifier

    def get(
        self,
        *,
        source: str,
        external_id: str,
        entity_type: str,
        namespace: str | None = None,
    ) -> ExternalIdentifier | None:
        return self._rows.get((source, external_id, entity_type, namespace))

    def list_for_entity(
        self, *, entity_type: str, genomeai_entity_id: str
    ) -> list[ExternalIdentifier]:
        return [
            row
            for row in self._rows.values()
            if row.entity_type == entity_type
            and str(row.genomeai_entity_id) == genomeai_entity_id
        ]

    def list_by_source(self, *, source: str) -> list[ExternalIdentifier]:
        return [row for row in self._rows.values() if row.source == source]


def _identifier(**overrides: object) -> ExternalIdentifier:
    values: dict[str, object] = {
        "source": "genomeai-reference",
        "external_id": "REF:1001",
        "entity_type": "gene",
        "genomeai_entity_id": uuid.uuid4(),
    }
    values.update(overrides)
    return ExternalIdentifier(**values)  # type: ignore[arg-type]


def test_create_and_get_identifier() -> None:
    store: ExternalIdentifierStore = InMemoryIdentifierStore()
    created = store.create(_identifier())
    fetched = store.get(
        source=created.source,
        external_id=created.external_id,
        entity_type=created.entity_type,
    )
    assert fetched == created


def test_duplicate_identifier_rejected() -> None:
    store = InMemoryIdentifierStore()
    store.create(_identifier())
    with pytest.raises(ValueError, match="duplicate"):
        store.create(_identifier())


def test_same_external_id_in_different_namespaces_allowed() -> None:
    store = InMemoryIdentifierStore()
    plain = store.create(_identifier(namespace=None))
    namespaced = store.create(_identifier(namespace="legacy"))
    assert plain.namespace is None
    assert namespaced.namespace == "legacy"


def test_entity_mapping_aggregates_cross_database_ids() -> None:
    store = InMemoryIdentifierStore()
    internal_id = uuid.uuid4()
    ncbi = store.create(
        _identifier(source="ncbi-gene", external_id="7157", genomeai_entity_id=internal_id)
    )
    ensembl = store.create(
        _identifier(
            source="ensembl-gene",
            external_id="ENSG00000141510",
            genomeai_entity_id=internal_id,
        )
    )
    mapped = store.list_for_entity(entity_type="gene", genomeai_entity_id=str(internal_id))
    assert {m.source for m in mapped} == {"ncbi-gene", "ensembl-gene"}
    assert ncbi.external_id == "7157"
    assert ensembl.external_id == "ENSG00000141510"
