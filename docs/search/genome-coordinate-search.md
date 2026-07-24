# Genome Coordinate Search

## Overview

Genome Coordinate Search provides reusable genomic interval searching that works across any biological domain model with coordinate columns (chromosome, start, end).

## Architecture

```
Service → Repository → coordinate_intervals.apply_coordinate_filter()
                           ↓
                    SQLAlchemy WHERE clause
                     (chromosome + interval)
```

## Supported Operations

| Operation     | SQL Logic                                                |
|---------------|----------------------------------------------------------|
| `exact`       | `chrom = q_chrom AND start = q_start AND end = q_end`    |
| `contains`    | `chrom = q_chrom AND start <= q_start AND end >= q_end`  |
| `contained_by`| `chrom = q_chrom AND start >= q_start AND end <= q_end`  |
| `overlap`     | `chrom = q_chrom AND start <= q_end AND end >= q_start`  |
| `range`       | `chrom = q_chrom AND start >= q_start AND end <= q_end`  |

## Modules

| Module                  | Location                                         | Responsibility                    |
|-------------------------|--------------------------------------------------|-----------------------------------|
| `coordinate_types.py`   | `genomeai_api/search/coordinate_types.py`        | `CoordinateMatchType`, `CoordinateInterval` |
| `coordinate_validation.py` | `genomeai_api/search/coordinate_validation.py` | Chromosome/coordinate/interval validation |
| `coordinate_intervals.py`  | `genomeai_api/search/coordinate_intervals.py`  | SQLAlchemy interval filter builder |
| `coordinate_search.py`  | `genomeai_api/search/coordinate_search.py`       | Re-exports for convenience        |

## Column Configuration

Each model maps its coordinate columns differently:

| Model      | Chromosome Column | Start Column     | End Column       |
|------------|-------------------|------------------|------------------|
| Gene       | `chromosome`      | `start_position` | `end_position`   |
| Variant    | `chromosome`      | `position`       | `position`       |
| Transcript | `chromosome`      | `start_position` | `end_position`   |

Default column names (`chromosome`, `start_position`, `end_position`) can be overridden per request via `chromosome_column`, `start_column`, `end_column`.

For single-position models like Variant, set both `start_column` and `end_column` to the same column (e.g., `position`).

## Usage

```python
from genomeai_api.services.search import SearchService
from genomeai_api.schemas.search import (
    CoordinateIntervalModel,
    CoordinateSearchRequest,
)
from genomeai_api.models.gene import Gene

service = SearchService(session)

request = CoordinateSearchRequest(
    interval=CoordinateIntervalModel(
        chromosome="chr1",
        start=10000,
        end=20000,
    ),
    match_type="overlap",
    pagination=PaginationRequest(page=1, page_size=20),
    sort=SortRequest(sort_by="gene_name", sort_order="asc"),
    filters=[FilterRule(field="biotype", operator="equals", value="protein_coding")],
)

result = await service.coordinate_search(Gene, request)
```

### Variant example (single position):

```python
request = CoordinateSearchRequest(
    interval=CoordinateIntervalModel(chromosome="chr1", start=150, end=150),
    match_type="exact",
    start_column="position",
    end_column="position",
)
result = await service.coordinate_search(Variant, request)
```

## Validation

- Chromosome format: `1-22`, `X`, `Y`, `MT`, `M` with optional `chr` prefix
- Coordinates must be non-negative integers
- Start must not exceed end
- Match type must be one of: `exact`, `contains`, `contained_by`, `overlap`, `range`

## Extension Guide

To add coordinate search to a new model:

1. Ensure the model has chromosome and start/end columns
2. Pass the model and column names to `coordinate_search()`
3. The existing infrastructure handles pagination, sorting, and filtering

## Future Indexing

For large-scale coordinate queries, consider:

- Brin indexes on chromosome + start_position
- GiST indexes using PostgreSQL range types
- Composite B-tree indexes on (chromosome, start_position, end_position)
