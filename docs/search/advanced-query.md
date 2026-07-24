# Advanced Query Engine

## Overview

The Advanced Query Engine extends GenomeAI's search infrastructure with a composable, SQLAlchemy-native expression system for building complex filter predicates. It supports nested AND/OR/NOT groups, 16 comparison operators, and full validation — all without raw SQL.

```
API Request (AdvancedFilterGroup JSON)
    ↓
Schema Validation (Pydantic)
    ↓
Expression Conversion (_convert_to_expression)
    ↓
Validation (expression tree, field names, operators, values)
    ↓
Query Builder (SQLAlchemy ClauseElement compilation)
    ↓
Repository Integration (.where() on existing stmt)
```

## Architecture

### Expression Tree (`search/expressions.py`)

Two immutable expression types:

```python
@dataclass(frozen=True)
class LeafExpression:
    field: str          # mapped column name
    operator: Operator   # one of 16 operators
    value: Any = None    # operand value

@dataclass(frozen=True)
class GroupExpression:
    connector: Literal["AND", "OR"] = "AND"
    children: tuple[LeafExpression | GroupExpression, ...]
    negated: bool = False
```

### Operators (`search/operators.py`)

| Category | Operators |
|----------|-----------|
| Comparison | `equals`, `not_equals`, `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal` |
| Range | `between` |
| Set | `in`, `not_in` |
| Null | `is_null`, `is_not_null` |
| String | `like`, `ilike`, `starts_with`, `ends_with`, `contains` |

### Validation (`search/validation.py`)

Validation covers:

- **Field names** — verified against SQLAlchemy `mapper.column_attrs`
- **Operator compatibility** — `between`/`in`/`not_in` require list values; `is_null`/`is_not_null` ignore values; all others require non-null values
- **List arity** — `between` needs exactly 2 values; `in`/`not_in` require non-empty lists
- **Recursion depth** — maximum 10 nested levels (configurable via `MAX_RECURSION_DEPTH`)
- **Expression count** — maximum 200 total expressions (configurable via `MAX_EXPRESSIONS`)
- **Connector validity** — only `"AND"` and `"OR"` are accepted

### Query Builder (`search/query_builder.py`)

`build_clause()` compiles the expression tree into a `ColumnElement[bool]` using only SQLAlchemy expression APIs:

- AND groups → `sqlalchemy.and_()`
- OR groups → `sqlalchemy.or_()`
- Negated groups → `sqlalchemy.not_()`
- Leaf expressions → `column == value`, `column.in_(value)`, `column.is_(None)`, `column.contains(value)`, etc.

### Schema Layer (`schemas/search.py`)

Added to `SearchRequest`:

```python
class AdvancedFilterRule(BaseModel):
    field: str
    operator: AdvancedFilterOperator  # Literal of all 16 operators
    value: Any = None

class AdvancedFilterGroup(BaseModel):
    connector: Literal["AND", "OR"] = "AND"
    children: list[AdvancedFilterRule | AdvancedFilterGroup]
    negated: bool = False

class SearchRequest(BaseModel):
    pagination: PaginationRequest = ...
    sort: SortRequest | None = None
    filters: list[FilterRule] | None = None
    advanced_filters: AdvancedFilterGroup | None = None  # NEW
```

The `filters` field remains fully backward-compatible. `advanced_filters` is an optional alternative that supports nested groups and 16 operators.

## Examples

### Simple AND Group

```json
{
  "advanced_filters": {
    "connector": "AND",
    "children": [
      {"field": "study_name", "operator": "contains", "value": "cancer"},
      {"field": "status", "operator": "equals", "value": "active"}
    ]
  }
}
```

### OR Group

```json
{
  "advanced_filters": {
    "connector": "OR",
    "children": [
      {"field": "organism", "operator": "equals", "value": "human"},
      {"field": "organism", "operator": "equals", "value": "mouse"}
    ]
  }
}
```

### NOT Group (negation)

```json
{
  "advanced_filters": {
    "connector": "AND",
    "children": [
      {"field": "status", "operator": "equals", "value": "closed"}
    ],
    "negated": true
  }
}
```

### Nested AND + OR

```json
{
  "advanced_filters": {
    "connector": "AND",
    "children": [
      {"field": "study_name", "operator": "contains", "value": "cancer"},
      {
        "connector": "OR",
        "children": [
          {"field": "status", "operator": "equals", "value": "active"},
          {"field": "status", "operator": "equals", "value": "pending"}
        ]
      }
    ]
  }
}
```

### BETWEEN + IS NULL

```json
{
  "advanced_filters": {
    "connector": "AND",
    "children": [
      {"field": "start_date", "operator": "between", "value": ["2020-01-01", "2023-12-31"]},
      {"field": "description", "operator": "is_not_null"}
    ]
  }
}
```

### Combined with Simple Filters

Simple filters and advanced filters may be combined. When both are present, all conditions are AND-ed together:

```json
{
  "filters": [
    {"field": "study_name", "operator": "contains", "value": "cancer"}
  ],
  "advanced_filters": {
    "connector": "AND",
    "children": [
      {"field": "status", "operator": "not_equals", "value": "closed"}
    ]
  }
}
```

## Extension Guide

### Adding a New Operator

1. Add the operator to the `Operator` enum in `search/operators.py`
2. Add it to the appropriate category frozen set (e.g., `COMPARISON_OPERATORS`)
3. Add the string literal to `AdvancedFilterOperator` in `schemas/search.py`
4. Add the operator mapping in `_build_leaf_clause()` in `search/query_builder.py`
5. If the operator requires special value validation, update `validate_operator_value()` in `search/validation.py`
6. Add tests for the new operator in `tests/test_advanced_query.py`

### Adding a New Model

No changes needed — the advanced query engine works generically with any SQLAlchemy `DeclarativeBase` model. Validation uses `inspect(model).column_attrs` to detect mapped columns dynamically.

### Custom Validation

The `validate_expression()` function accepts any `DeclarativeBase` subclass, making it reusable for domain-specific validation. Override `MAX_RECURSION_DEPTH` or `MAX_EXPRESSIONS` by importing and patching them.

## Security

The Advanced Query Engine uses SQLAlchemy expression APIs exclusively:

- **No string interpolation** — all user input is passed as bound parameters
- **No raw SQL** — all clauses use `column.op()`, `and_()`, `not_()`, etc.
- **Field whitelisting** — validation rejects any field not in `mapper.column_attrs`
- **Recursion limits** — depth and count limits prevent DoS via deeply nested expressions
