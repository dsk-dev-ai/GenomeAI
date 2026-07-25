from __future__ import annotations

import asyncio
from typing import Any

INDEX_MAPPINGS: dict[str, dict[str, Any]] = {
    "study": {
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
    },
    "gene": {
        "properties": {
            "id": {"type": "keyword"},
            "gene_id": {"type": "keyword"},
            "gene_symbol": {"type": "text"},
            "gene_name": {"type": "text"},
            "chromosome": {"type": "keyword"},
            "start_position": {"type": "long"},
            "end_position": {"type": "long"},
            "strand": {"type": "keyword"},
            "biotype": {"type": "keyword"},
            "description": {"type": "text"},
        }
    },
    "variant": {
        "properties": {
            "id": {"type": "keyword"},
            "variant_id": {"type": "keyword"},
            "chromosome": {"type": "keyword"},
            "position": {"type": "long"},
            "reference": {"type": "keyword"},
            "alternate": {"type": "keyword"},
            "quality": {"type": "float"},
            "filter": {"type": "keyword"},
            "gene_symbol": {"type": "keyword"},
            "consequence": {"type": "keyword"},
        }
    },
    "sample": {
        "properties": {
            "id": {"type": "keyword"},
            "sample_id": {"type": "keyword"},
            "study_id": {"type": "keyword"},
            "organism": {"type": "keyword"},
            "tissue": {"type": "keyword"},
            "disease_state": {"type": "keyword"},
            "collection_date": {"type": "date"},
        }
    },
    "experiment": {
        "properties": {
            "id": {"type": "keyword"},
            "experiment_id": {"type": "keyword"},
            "study_id": {"type": "keyword"},
            "experiment_type": {"type": "keyword"},
            "platform": {"type": "keyword"},
            "assay": {"type": "keyword"},
            "date_performed": {"type": "date"},
            "description": {"type": "text"},
        }
    },
    "dataset": {
        "properties": {
            "id": {"type": "keyword"},
            "dataset_id": {"type": "keyword"},
            "study_id": {"type": "keyword"},
            "name": {"type": "text"},
            "description": {"type": "text"},
            "data_type": {"type": "keyword"},
            "file_format": {"type": "keyword"},
            "file_size": {"type": "long"},
            "accession": {"type": "keyword"},
        }
    },
    "project": {
        "properties": {
            "id": {"type": "keyword"},
            "project_id": {"type": "keyword"},
            "name": {"type": "text"},
            "description": {"type": "text"},
            "pi": {"type": "keyword"},
            "institution": {"type": "keyword"},
            "funding_source": {"type": "keyword"},
            "start_date": {"type": "date"},
            "end_date": {"type": "date"},
            "status": {"type": "keyword"},
        }
    },
    "genome": {
        "properties": {
            "id": {"type": "keyword"},
            "genome_id": {"type": "keyword"},
            "assembly": {"type": "keyword"},
            "species": {"type": "keyword"},
            "genome_build": {"type": "keyword"},
            "gc_content": {"type": "float"},
            "total_length": {"type": "long"},
            "description": {"type": "text"},
        }
    },
    "transcript": {
        "properties": {
            "id": {"type": "keyword"},
            "transcript_id": {"type": "keyword"},
            "gene_id": {"type": "keyword"},
            "gene_symbol": {"type": "keyword"},
            "transcript_name": {"type": "text"},
            "biotype": {"type": "keyword"},
            "chromosome": {"type": "keyword"},
            "start_position": {"type": "long"},
            "end_position": {"type": "long"},
        }
    },
    "protein": {
        "properties": {
            "id": {"type": "keyword"},
            "protein_id": {"type": "keyword"},
            "transcript_id": {"type": "keyword"},
            "gene_symbol": {"type": "keyword"},
            "protein_name": {"type": "text"},
            "sequence_length": {"type": "long"},
            "molecular_weight": {"type": "float"},
            "isoelectric_point": {"type": "float"},
        }
    },
}

SUPPORTED_INDEX_TYPES: frozenset[str] = frozenset(INDEX_MAPPINGS.keys())


async def create_index(
    backend: Any,
    index: str,
    mappings: dict[str, Any] | None = None,
) -> None:
    if index not in SUPPORTED_INDEX_TYPES:
        supported = ", ".join(sorted(SUPPORTED_INDEX_TYPES))
        msg = f"Unsupported index type '{index}'. Supported: {supported}"
        raise ValueError(msg)
    if not hasattr(backend, "_get_client"):
        msg = "Backend does not support index creation"
        raise NotImplementedError(msg)
    client = backend._get_client()
    full_index = f"{backend._index_prefix}_{index}"
    resolved_mappings = mappings if mappings is not None else INDEX_MAPPINGS.get(index, {})
    body: dict[str, Any] = {"mappings": resolved_mappings}
    await asyncio.to_thread(lambda: client.indices.create(index=full_index, body=body))


async def delete_index(backend: Any, index: str) -> None:
    if not hasattr(backend, "_get_client"):
        msg = "Backend does not support index deletion"
        raise NotImplementedError(msg)
    client = backend._get_client()
    full_index = f"{backend._index_prefix}_{index}"
    await asyncio.to_thread(
        lambda: client.indices.delete(index=full_index, ignore_unavailable=True)
    )


async def index_exists(backend: Any, index: str) -> bool:
    if not hasattr(backend, "_get_client"):
        msg = "Backend does not support index operations"
        raise NotImplementedError(msg)
    client = backend._get_client()
    full_index = f"{backend._index_prefix}_{index}"
    return await asyncio.to_thread(lambda: client.indices.exists(index=full_index))
