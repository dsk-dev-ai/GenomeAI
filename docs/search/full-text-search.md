# PostgreSQL Full-Text Search

## Overview

PostgreSQL provides native full-text search through `tsvector` and `tsquery` data types. GenomeAI exposes these via SQLAlchemy function expressions.

## Search Pipeline

```
User Query
    ↓
build_tsquery() → tsquery (parsed search terms)
build_tsvector() → tsvector (weighted document columns)
    ↓
vector @@ query  (match operator)
    ↓
ts_rank() / ts_rank_cd()  (relevance scoring)
    ↓
ts_headline()  (highlighted snippets)
    ↓
ORDER BY rank DESC + PK tiebreaker
    ↓
Pagination (offset/limit)
```

## Usage

### Basic FTS

```python
from genomeai_api.search.fts import build_tsvector, build_tsquery
from genomeai_api.search.query import apply_fts_to_statement
from sqlalchemy import select

stmt = select(MyModel)
stmt = apply_fts_to_statement(
    stmt, MyModel,
    columns=["name", "description"],
    search_query="cancer research",
)
```

### With Weights

```python
stmt = apply_fts_to_statement(
    stmt, MyModel,
    columns=["name", "description"],
    search_query="cancer",
    weights=["A", "B"],  # A = high priority, B = normal
)
```

### Query Types

| Type | Function | Example Input |
|------|----------|--------------|
| `plain` | `plainto_tsquery()` | `"cancer research"` |
| `phrase` | `phraseto_tsquery()` | `"cancer research"` |
| `websearch` | `websearch_to_tsquery()` | `"cancer research"` |
| `raw` | `to_tsquery()` | `"cancer & research"` |

## Indexes

For production performance, create GIN indexes:

```python
from genomeai_api.search.indexes import create_gin_index

idx = create_gin_index(
    "ix_mytable_name_gin",
    "my_table",
    "name",
)
```

Or use computed TSVECTOR columns:

```python
from genomeai_api.search.indexes import create_tsvector_column

col = create_tsvector_column(
    "tsv",
    "to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))",
)
```
