# Ranking Strategy

## Relevance Scoring

GenomeAI uses PostgreSQL's native ranking functions:

### ts_rank()

Standard relevance ranking based on term frequency:

```python
from genomeai_api.search.ranking import apply_ts_rank

stmt = apply_ts_rank(stmt, vector, query, label="rank", normalization=0)
```

### ts_rank_cd()

Cover density ranking — considers how close matching terms are to each other:

```python
from genomeai_api.search.ranking import apply_ts_rank_cd

stmt = apply_ts_rank_cd(stmt, vector, query, label="rank", normalization=0)
```

## Normalization Options

| Value | Effect |
|-------|--------|
| `0` | No normalization (default) |
| `1` | Divide by 1 + log(document length) |
| `2` | Divide by document length |
| `4` | Divide by mean harmonic distance |
| `8` | Divide by number of unique words |
| `16` | Divide by 1 + log(number of unique words) |
| `32` | `rank / (rank + 1)` |

Combine via bitwise OR: `1 | 4` = `5`

## Result Ordering

FTS results are ordered by:

1. **Primary**: Rank descending (most relevant first)
2. **Tiebreaker**: Primary key ascending (deterministic pagination)

```python
from genomeai_api.search.ranking import order_by_rank_desc
from genomeai_api.repositories.search import _ensure_deterministic_ordering

stmt = order_by_rank_desc(stmt, rank_label="rank")
stmt = stmt.order_by(pk_column.asc())  # tiebreaker
```

## Weighted Columns

Control per-column importance using PostgreSQL `setweight()`:

| Weight | Default multiplier | Typical Use |
|--------|--------------------|------------|
| `A` | 1.0 | Titles, names, identifiers |
| `B` | 0.4 | Keywords, symbols |
| `C` | 0.2 | Descriptions, abstracts |
| `D` | 0.1 | Body text, notes |

```python
vector = build_tsvector(
    [Model.name, Model.description],
    weights=["A", "D"],
)
```
