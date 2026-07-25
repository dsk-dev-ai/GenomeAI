# Query DSL

## Overview

The Query DSL provides a lightweight JSON query language that compiles into the Advanced Query Engine expression tree. It is designed for programmatic query construction where the full JSON structure is built by code rather than hand-written.

```
DSL JSON ("where" dict)
    ↓
DslSearchQuery Schema (Pydantic)
    ↓
DSL Compiler (compile_dsl → GroupExpression)
    ↓
Validation (expression tree, field names, operators, values)
    ↓
Query Builder (SQLAlchemy ClauseElement compilation)
    ↓
Repository Integration (.where() on existing stmt)
```

## Data Flow

1. **API Layer** receives a `DslSearchQuery` with a `where` field containing the DSL JSON
2. **DSL Compiler** (`compile_dsl`) recursively compiles the `where` tree into a `GroupExpression`
3. **Existing Validation** (`validate_expression`) validates field names, operators, and values
4. **Existing Query Builder** (`build_clause`) converts the expression tree to a SQLAlchemy `ClauseElement`
5. **DSL Repository** applies the clause to the query alongside any simple filters, sort, and pagination

## DSL Structure

### Leaf Condition (Single Filter)

```json
{"field": "study_name", "op": "eq", "value": "Cancer Study"}
```

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `field` | string | yes | Mapped column name on the model |
| `op` | string | yes | DSL operator (see table below) |
| `value` | any | varies | Operator value |

### AND / OR Groups

```json
{"and": [<condition>, <condition>, ...]}
{"or": [<condition>, <condition>, ...]}
```

### NOT

Wraps a single condition or group:

```json
{"not": {"field": "status", "op": "eq", "value": "archived"}}
{"not": {"and": [<condition>, <condition>]}}
```

## Operators

| DSL Op | Advanced Operator | Description | Value Type |
|--------|------------------|-------------|------------|
| `eq` | `EQUALS` | Equals | any |
| `ne` | `NOT_EQUALS` | Not equals | any |
| `gt` | `GREATER_THAN` | Greater than | any |
| `gte` | `GREATER_THAN_OR_EQUAL` | Greater than or equal | any |
| `lt` | `LESS_THAN` | Less than | any |
| `lte` | `LESS_THAN_OR_EQUAL` | Less than or equal | any |
| `between` | `BETWEEN` | Between inclusive | `[lo, hi]` (exactly 2) |
| `in` | `IN` | In list | `[...]` (non-empty) |
| `not_in` | `NOT_IN` | Not in list | `[...]` (non-empty) |
| `is_null` | `IS_NULL` | Is null | none |
| `is_not_null` | `IS_NOT_NULL` | Is not null | none |
| `like` | `LIKE` | SQL LIKE | string |
| `ilike` | `ILIKE` | Case-insensitive LIKE | string |
| `starts_with` | `STARTS_WITH` | Prefix match | string |
| `ends_with` | `ENDS_WITH` | Suffix match | string |
| `contains` | `CONTAINS` | Substring match | string |

## API Endpoints

### POST /api/v1/search/dsl

Universal DSL search across all entities.

**Request Body:**
```json
{
    "where": {
        "and": [
            {"field": "study_name", "op": "contains", "value": "Cancer"},
            {"field": "status", "op": "eq", "value": "active"}
        ]
    },
    "pagination": {"page": 1, "page_size": 20},
    "sort": {"sort_by": "study_name", "sort_order": "asc"},
    "filters": [{"field": "study_type", "operator": "equals", "value": "cohort"}]
}
```

### POST /api/v1/search/{domain}/dsl

Domain-scoped DSL search. The `{domain}` placeholder is replaced with a registered domain name (study, gene, variant, sample, experiment, dataset, project).

## Examples

### Simple Filter

```json
{"where": {"field": "status", "op": "eq", "value": "active"}}
```

### Nested AND/OR

```json
{
    "where": {
        "and": [
            {"field": "organism", "op": "eq", "value": "Homo sapiens"},
            {
                "or": [
                    {"field": "status", "op": "eq", "value": "active"},
                    {"field": "status", "op": "eq", "value": "pending"}
                ]
            },
            {"not": {"field": "description", "op": "is_null"}}
        ]
    }
}
```

### Range Query

```json
{"where": {"field": "created_at", "op": "between", "value": ["2020-01-01", "2024-01-01"]}}
```

## Validation Rules

| Rule | Error |
|------|-------|
| Empty `where` | `"DSL 'where' must not be empty"` |
| Non-dict `where` | `"DSL 'where' must be a dict"` |
| Unknown keys | `"Unknown key(s) at depth N: ..."` |
| Mixed logical + leaf keys | `"Mixed logical keys and field/op/value"` |
| No logical or leaf keys | `"must contain either a logical key or field/op/value"` |
| Multiple logical keys | `"Multiple logical keys"` |
| `not` with list value | `"'not' must be a single object"` |
| Missing operator | `"missing 'op'"` |
| Unsupported operator | `"Unsupported operator"` |
| Value type mismatch | `"requires a list value"` / `"does not accept a value"` |
| `between` requires 2 values | `"requires exactly 2 values"` |
| `in`/`not_in` requires non-empty | `"requires a non-empty list"` |
| Missing required value | `"requires a non-null value"` |
| Invalid field name | `"not a mapped column"` |
| Recursion depth > 10 | `"Maximum recursion depth exceeded"` |
| Expression count > 200 | `"Maximum expression count exceeded"` |
