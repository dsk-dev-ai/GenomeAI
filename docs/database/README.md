# Database Documentation

The storage layer is built (PostgreSQL 16+ with SQLAlchemy models, Redis 7+ for
queue/cache). See:

- [`apps/api/src/genomeai_api/models/`](../../apps/api/src/genomeai_api/models/) —
  domain model definitions
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md) — storage layer overview
- [`docs/data-integration/architecture.md`](../data-integration/architecture.md) —
  integration tables (raw records, provenance, external identifiers)
- [`docs/search/architecture.md`](../search/architecture.md) — search query architecture (full-text)

Planned future documents (when the schema reference is extracted):

| Document | Description |
|----------|-------------|
| `migrations.md` | Migration workflow and conventions |
| `queries.md` | Common query patterns and optimizations |
| `indexing.md` | Indexing strategy and performance tuning |