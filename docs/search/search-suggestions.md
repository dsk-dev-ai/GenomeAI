# Search Suggestions & Autocomplete

## Overview

The suggestions system provides real-time autocomplete suggestions across all 10 biological domains. It uses prefix matching with case-insensitive ranking and is backed by a pluggable cache layer.

## Architecture

```
Route (GET /search/suggestions)
  → SearchService.suggest()
    → Cache lookup (if available)
      → Repository: execute_suggestions()
        → Autocomplete: build_prefix_query()
          → Database
      → Suggestions: rank_suggestions()
    → SuggestionResponse
```

## API

### GET /search/suggestions

**Parameters**

| Parameter | Type   | Default  | Constraints         | Description                       |
|-----------|--------|----------|---------------------|-----------------------------------|
| query     | string | required | 1–200 chars         | Search prefix                     |
| limit     | int    | 10       | 1–100               | Max results                       |
| domain    | string | "study"  | One of 10 domains   | Biological domain to suggest on   |
| field     | string | —        | Mapped column name  | Specific column (default per domain) |

**Response**

```json
{
  "suggestions": [
    {
      "domain": "study",
      "field": "study_name",
      "value": "Cancer Genomics Study",
      "rank": 0,
      "match_type": "exact"
    }
  ],
  "count": 1,
  "query": "cancer"
}
```

**match_type** values: `exact`, `prefix`, `alphabetical`

**Supported domains**: genome, sample, gene, variant, transcript, protein, experiment, dataset, study, project

**Default suggestion fields**:

| Domain     | Default Field        |
|------------|----------------------|
| genome     | accession            |
| sample     | sample_name          |
| gene       | gene_name            |
| variant    | variant_id           |
| transcript | transcript_name      |
| protein    | protein_name         |
| experiment | experiment_name      |
| dataset    | dataset_name         |
| study      | study_name           |
| project    | project_name         |

## Ranking

Suggestions are ranked by:

1. **Exact match** (case-insensitive)
2. **Prefix match** (starts with, case-insensitive)
3. **Alphabetical** (fallback, ascending)

Deterministic ordering ensures the same query always returns identical results.

## Cache Layer

The `SuggestionCache` abstract class supports pluggable backends:

| Implementation | Description                    |
|----------------|--------------------------------|
| `NullCache`    | No-op (default)                |
| `MemoryCache`  | In-memory store (for testing)  |

Custom backends (e.g., Redis) implement `SuggestionCache`.

### Cache Keys

Format: `suggest:{domain}:{field}:{query}:{limit}`

## Modules

| Module         | Location                                   | Responsibility                    |
|----------------|--------------------------------------------|-----------------------------------|
| cache.py       | `genomeai_api/search/cache.py`             | Cache abstraction + null/memory   |
| suggestions.py | `genomeai_api/search/suggestions.py`       | Data model + ranking              |
| autocomplete.py| `genomeai_api/search/autocomplete.py`      | Prefix query builder              |

## Usage

```python
from genomeai_api.services.search import SearchService
from genomeai_api.models.gene import Gene

service = SearchService(session)
result = await service.suggest(
    model=Gene,
    column_name="gene_name",
    query="brca",
    limit=10,
    domain="gene",
)
```

## Testing

```bash
pytest tests/test_search_suggestions.py -v
```
