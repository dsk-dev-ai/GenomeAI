# Search Architecture

## Overview

GenomeAI's search system provides a generic, reusable search infrastructure that powers all biological domains. The architecture follows a layered design:

```
API Layer (Routes)
    ↓
Search Schemas (Pydantic)
    ↓
Search Service (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Search Package (FTS Utilities)
    ↓
SQLAlchemy / PostgreSQL
```

## Core Components

### Search Package (`genomeai_api/search/`)

The search package provides PostgreSQL Full-Text Search (FTS) utilities:

| Module | Purpose |
|--------|---------|
| `fts.py` | Build `tsvector` and `tsquery` expressions |
| `query.py` | Apply FTS filters to SQLAlchemy statements |
| `ranking.py` | Compute and sort by relevance scores |
| `highlighting.py` | Generate `ts_headline` result snippets |
| `indexes.py` | Create GIN indexes and computed TSVECTOR columns |

### Schema Layer (`genomeai_api/schemas/search.py`)

Defines request/response models:

- `SearchRequest` — pagination, sorting, filtering
- `FullTextSearchConfig` — FTS-specific query parameters
- `FullTextSearchRequest` — combined search + FTS request
- `FullTextSearchResponse` — search results with ranks and highlights

### Repository Layer (`genomeai_api/repositories/search.py`)

Provides generic search execution:

- `execute_search()` — standard filtered/sorted/paginated search
- `execute_fts_search()` — full-text search with ranking and highlighting
- `SearchResult` / `FTSResult` — generic result containers

### Service Layer (`genomeai_api/services/search.py`)

`SearchService` wraps repository functions into async service methods:

- `search()` — standard search
- `search_fts()` — full-text search with rank/highlight conversion

## Design Principles

1. **Generic by default**: All search utilities work with any SQLAlchemy model
2. **No domain coupling**: No Gene, Protein, or Variant-specific code
3. **Composable**: Each utility function composes with standard SQLAlchemy queries
4. **Type-safe**: Full mypy/pyright compliance with generic type parameters
