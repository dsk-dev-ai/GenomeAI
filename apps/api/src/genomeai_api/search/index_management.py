from __future__ import annotations

from typing import Any

DEFAULT_MAPPINGS: dict[str, Any] = {
    "properties": {
        "id": {"type": "keyword"},
        "study_id": {"type": "keyword"},
        "study_name": {"type": "text"},
        "study_type": {"type": "keyword"},
        "title": {"type": "text"},
        "description": {"type": "text"},
        "organism": {"type": "keyword"},
        "institution": {"type": "keyword"},
        "principal_investigator": {"type": "keyword"},
        "publication": {"type": "text"},
        "doi": {"type": "keyword"},
        "status": {"type": "keyword"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
    }
}

SUPPORTED_INDEX_TYPES: frozenset[str] = frozenset({
    "study",
    "gene",
    "variant",
    "sample",
    "experiment",
    "dataset",
    "project",
    "genome",
    "transcript",
    "protein",
})


async def create_index(
    backend: Any,
    index: str,
    mappings: dict[str, Any] | None = None,
) -> None:
    if index not in SUPPORTED_INDEX_TYPES:
        supported = ", ".join(sorted(SUPPORTED_INDEX_TYPES))
        msg = f"Unsupported index type '{index}'. Supported: {supported}"
        raise ValueError(msg)
    try:
        client = backend._get_client()
    except AttributeError:
        msg = "Backend does not support index creation"
        raise NotImplementedError(msg)
    full_index = f"{backend._index_prefix}_{index}"
    body: dict[str, Any] = {"mappings": mappings or DEFAULT_MAPPINGS}
    client.indices.create(index=full_index, body=body)


async def delete_index(backend: Any, index: str) -> None:
    try:
        client = backend._get_client()
    except AttributeError:
        msg = "Backend does not support index deletion"
        raise NotImplementedError(msg)
    full_index = f"{backend._index_prefix}_{index}"
    client.indices.delete(index=full_index, ignore_unavailable=True)


async def index_exists(backend: Any, index: str) -> bool:
    try:
        client = backend._get_client()
    except AttributeError:
        msg = "Backend does not support index operations"
        raise NotImplementedError(msg)
    full_index = f"{backend._index_prefix}_{index}"
    return client.indices.exists(index=full_index)
