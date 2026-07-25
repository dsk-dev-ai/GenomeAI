# Domain Search

Reusable domain-specific search endpoints backed by the generic search infrastructure.

## Architecture

```text
POST /search/{domain}       → SearchService.domain_search()       → execute_search()
POST /search/{domain}/fts   → SearchService.domain_search_fts()   → execute_fts_search()
POST /search/{domain}/coordinate → SearchService.coordinate_search() → execute_coordinate_search()

Each domain is configured by a DomainSearchConfig that declares:
  • model           – SQLAlchemy model class
  • search_fields   – columns searched when q= is provided
  • fts_fields      – columns indexed for full-text search
  • fts_weights     – weight labels (A/B/C/D) matching fts_fields
  • suggestion_field – default field for autocomplete
  • coordinate_*    – column mapping for coordinate search (where applicable)
```

## Supported Domains

| Domain      | Endpoint                 | Search Fields                                             | FTS Columns              | Coordinate |
|-------------|--------------------------|-----------------------------------------------------------|--------------------------|------------|
| gene        | `/search/gene`           | gene_id, gene_name, description                           | gene_name, description   | ✅         |
| protein     | `/search/protein`        | protein_id, protein_name, accession, symbol, description  | protein_name, description, function | ❌ |
| variant     | `/search/variant`        | variant_id, chromosome, ref, alt, description             | variant_id, ref, alt, description | ✅ (single position) |
| transcript  | `/search/transcript`     | transcript_id, transcript_name, description                | transcript_name, description | ✅ |
| genome      | `/search/genome`         | accession, organism, assembly, description                | accession, organism, assembly, description | ❌ |
| study       | `/search/study`          | study_id, study_name, title, description                  | title, description       | ❌ |
| sample      | `/search/sample`         | sample_id, sample_name, description                       | sample_name, description | ❌ |
| dataset     | `/search/dataset`        | dataset_id, dataset_name, description                     | dataset_name, description | ❌ |
| experiment  | `/search/experiment`     | experiment_id, experiment_name, description               | experiment_name, description | ❌ |
| project     | `/search/project`        | project_id, project_name, description                     | project_name, description | ❌ |

## Usage

### Basic keyword search

Searches across all search\_fields of the domain using `CONTAINS`:

```python
import httpx

response = httpx.post(
    "http://localhost:8000/search/gene",
    json={"q": "BRCA1", "pagination": {"page": 1, "page_size": 20}},
)
```

### With filters, sorting, and pagination

```python
response = httpx.post(
    "http://localhost:8000/search/gene",
    json={
        "q": "BRCA",
        "filters": [{"field": "biotype", "operator": "equals", "value": "protein_coding"}],
        "sort": {"sort_by": "gene_name", "sort_order": "asc"},
        "pagination": {"page": 1, "page_size": 50},
    },
)
```

### Full-text search

```python
response = httpx.post(
    "http://localhost:8000/search/gene/fts",
    json={
        "search": {
            "filters": [{"field": "biotype", "operator": "equals", "value": "protein_coding"}],
        },
        "fts": {
            "query": "BRCA1",
            "columns": ["gene_name", "description"],
            "config": "english",
        },
    },
)
```

### Coordinate search (gene, variant, transcript only)

```python
response = httpx.post(
    "http://localhost:8000/search/gene/coordinate",
    json={
        "interval": {"chromosome": "chr1", "start": 10000, "end": 20000},
        "match_type": "overlap",
        "pagination": {"page": 1, "page_size": 20},
    },
)
```

### Variant single-position coordinate search

```python
response = httpx.post(
    "http://localhost:8000/search/variant/coordinate",
    json={
        "interval": {"chromosome": "chr1", "start": 150, "end": 150},
        "match_type": "exact",
        "start_column": "position",
        "end_column": "position",
    },
)
```

## DomainSearchRequest

The `DomainSearchRequest` model extends `SearchRequest` with an optional `q` field:

| Field            | Type                          | Default  | Description                            |
|------------------|-------------------------------|----------|----------------------------------------|
| q                | `str \| None`                 | `null`   | Keyword to search across domain fields |
| pagination       | `PaginationRequest`           | page=1, page_size=20 | Pagination             |
| sort             | `SortRequest \| None`         | `null`   | Sorting specification                  |
| filters          | `list[FilterRule] \| None`    | `null`   | Simple filters                         |
| advanced_filters | `AdvancedFilterGroup \| None` | `null`   | Advanced filter expressions            |

## Extension Guide

To add a new domain:

```python
from genomeai_api.models.mymodel import MyModel
from genomeai_api.routes.search import DOMAIN_MAP
from genomeai_api.search.domain_search import DomainSearchConfig, DOMAIN_SEARCH_CONFIGS

MY_SEARCH = DomainSearchConfig(
    model=MyModel,
    search_fields=["field1", "field2"],
    fts_fields=["field1"],
    fts_weights=["A"],
    suggestion_field="field1",
    has_coordinate_search=True,
    coordinate_chromosome_column="chromosome",
    coordinate_start_column="start_position",
    coordinate_end_column="end_position",
)

DOMAIN_SEARCH_CONFIGS["mymodel"] = MY_SEARCH
DOMAIN_MAP["mymodel"] = MyModel
```

Both `DOMAIN_SEARCH_CONFIGS` and `DOMAIN_MAP` must be updated to activate search endpoints and coordinate search for the new domain.
