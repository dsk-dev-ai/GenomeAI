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

For production performance, create GIN expression indexes that exactly mirror the runtime `build_tsvector()` expression.

### Single-column expression index

Runtime builds:

```sql
to_tsvector('english', coalesce(name, ''))
```

Create the matching index:

```sql
CREATE INDEX ix_mytable_name_fts
ON my_table
USING GIN (to_tsvector('english', coalesce(name, '')));
```

### Multi-column expression index

Runtime builds:

```sql
to_tsvector('english', coalesce(name, ''))
||
to_tsvector('english', coalesce(description, ''))
```

Create the matching index:

```sql
CREATE INDEX ix_mytable_name_desc_fts
ON my_table
USING GIN (
    to_tsvector('english', coalesce(name, ''))
    ||
    to_tsvector('english', coalesce(description, ''))
);
```

### Weighted expression index

Runtime builds with weights:

```sql
setweight(to_tsvector('english', coalesce(name, '')), 'A')
||
setweight(to_tsvector('english', coalesce(description, '')), 'B')
```

Create the matching index:

```sql
CREATE INDEX ix_mytable_weighted_fts
ON my_table
USING GIN (
    setweight(to_tsvector('english', coalesce(name, '')), 'A')
    ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B')
);
```

### Alembic migration example

```python
import sqlalchemy as sa
from alembic import op


def upgrade() -> None:
    op.create_index(
        "ix_mytable_name_fts",
        "my_table",
        [
            sa.text(
                "to_tsvector('english', coalesce(name, ''))"
            ),
        ],
        postgresql_using="gin",
    )
```
