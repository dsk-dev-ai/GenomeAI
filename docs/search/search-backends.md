# Search Backends

## Architecture

The search backend architecture provides a pluggable interface for multiple search engines behind a common abstraction.

```
SearchService
    │
    ▼
SearchBackend (ABC)
    │
    ├── PostgresBackend (default)
    ├── OpenSearchBackend (optional)
    └── ElasticsearchBackend (optional)
```

The `SearchService` accepts an optional `SearchBackend` instance. If none is provided, a `PostgresBackend` is created automatically, preserving the existing behavior.

## Backend Interface

All backends implement the `SearchBackend` ABC:

| Method | Description |
|--------|-------------|
| `search()` | Basic paginated/filtered/sorted search |
| `search_fts()` | Full-text search with ranking |
| `suggest()` | Autocomplete suggestions |
| `coordinate_search()` | Genomic coordinate interval search |
| `health_check()` | Backend connectivity check |
| `index_document()` | Index a single document |
| `update_document()` | Update an existing document |
| `delete_document()` | Delete a document |
| `bulk_index()` | Bulk index multiple documents |

## Backends

### PostgreSQL (Default)

Wraps the existing repository layer. No additional configuration required.

- Uses SQLAlchemy + asyncpg
- Supports all existing features: FTS, suggestions, coordinate search, advanced filters, DSL
- Index operations raise `NotImplementedError`

### OpenSearch (Optional)

Uses the official `opensearch-py` client.

- Lazy connection initialization
- Supports index CRUD operations
- Search methods raise `NotImplementedError` (use native OpenSearch DSL directly)

### Elasticsearch (Optional)

Uses the official `elasticsearch` Python client.

- Lazy connection initialization
- Supports index CRUD operations
- Search methods raise `NotImplementedError` (use native ES DSL directly)

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_BACKEND` | `postgres` | Backend selection: `postgres`, `opensearch`, `elasticsearch` |
| `SEARCH_URL` | `http://localhost:9200` | Backend server URL |
| `SEARCH_USERNAME` | None | Authentication username |
| `SEARCH_PASSWORD` | None | Authentication password |
| `SEARCH_INDEX_PREFIX` | `genomeai` | Prefix for index names |

## Usage

### Programmatic Backend Selection

```python
from genomeai_api.search.backends.factory import create_backend
from genomeai_api.search.config import BackendConfig
from genomeai_api.services.search import SearchService

# PostgreSQL (default)
service = SearchService(session)

# OpenSearch
config = BackendConfig(
    backend="opensearch",
    url="https://opensearch:9200",
    index_prefix="genomeai",
)
backend = create_backend(config)
service = SearchService(session, backend=backend)

# Elasticsearch
config = BackendConfig(
    backend="elasticsearch",
    url="https://elasticsearch:9200",
)
backend = create_backend(config)
service = SearchService(session, backend=backend)
```

### Index Management

```python
from genomeai_api.search.index_management import create_index, delete_index, index_exists

backend = create_backend(BackendConfig(backend="opensearch"))

# Create index with default mappings
await create_index(backend, "study")

# Create index with custom mappings
custom = {"properties": {"my_field": {"type": "text"}}}
await create_index(backend, "gene", custom)

# Check if index exists
exists = await index_exists(backend, "study")

# Delete index
await delete_index(backend, "study")
```

## Fallback Behavior

If `SEARCH_BACKEND` is not set or set to `postgres`, the system behaves exactly as before. No changes to existing APIs.

If `SEARCH_BACKEND` is set to `opensearch` or `elasticsearch` but the corresponding client package is not installed, an `ImportError` is raised when the backend is first used.

## Deployment Guide

### PostgreSQL (Default)

No changes required. Existing deployment works as-is.

### OpenSearch

1. Install the OpenSearch Python client:
   ```bash
   pip install genomeai-api[opensearch]
   ```

2. Set environment variables:
   ```bash
   export SEARCH_BACKEND=opensearch
   export SEARCH_URL=https://opensearch:9200
   export SEARCH_USERNAME=admin
   export SEARCH_PASSWORD=your_password
   export SEARCH_INDEX_PREFIX=genomeai
   ```

3. Create indexes using the index management helpers.

### Elasticsearch

1. Install the Elasticsearch Python client:
   ```bash
   pip install genomeai-api[elasticsearch]
   ```

2. Set environment variables:
   ```bash
   export SEARCH_BACKEND=elasticsearch
   export SEARCH_URL=https://elasticsearch:9200
   export SEARCH_INDEX_PREFIX=genomeai
   ```

## Migration Guide

### From PostgreSQL to OpenSearch/Elasticsearch

1. Install the required client package
2. Configure environment variables
3. Create indexes using `create_index()` for each model
4. Bulk index existing data using `bulk_index()`
5. Update `SEARCH_BACKEND` and restart

### Rolling Back

Revert `SEARCH_BACKEND` to `postgres` and restart. All existing PostgreSQL search functionality remains intact.

## Troubleshooting

| Issue | Resolution |
|-------|------------|
| `ImportError: opensearch-py is not installed` | Install with `pip install genomeai-api[opensearch]` |
| `ImportError: elasticsearch is not installed` | Install with `pip install genomeai-api[elasticsearch]` |
| `ValueError: PostgresBackend requires an AsyncSession` | Pass a session when creating PostgresBackend via the factory |
| `NotImplementedError: PostgresBackend does not support document indexing` | PostgreSQL backend uses relational tables, not document indexes |
| Connection refused | Verify backend URL and authentication credentials |
