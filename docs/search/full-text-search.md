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

For production performance, create GIN expression indexes that match the runtime `to_tsvector()` call exactly.

### Single-column expression index

```sql
CREATE INDEX ix_mytable_name_fts
ON my_table
USING GIN (to_tsvector('english', coalesce(name, '')));
```

### Multi-column expression index

```sql
CREATE INDEX ix_mytable_name_desc_fts
ON my_table
USING GIN (to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')));
```

### Alembic migration helper

Use Alembic's `op.create_index()` with `postgresql_using`:

```python
from alembic import op

def upgrade() -> None:
    op.create_index(
        "ix_mytable_name_fts",
        "my_table",
        [sa.text("to_tsvector('english', coalesce(name, ''))")],
        postgresql_using="gin",
    )
```

### Index utility functions

The `indexes` module provides helpers for creating GIN indexes on named columns:

```python
from genomeai_api.search.indexes import create_gin_index

idx = create_gin_index(
    "ix_mytable_name_gin",
    "my_table",
    "name",
)
```

> **Note**: `create_gin_index` creates an index on a raw column, not a TSVECTOR expression. For FTS performance, prefer the expression index approach shown above using Alembic's `sa.text()`.
