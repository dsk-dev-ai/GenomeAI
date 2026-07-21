# ADR 003: Knowledge Graph Storage Model

**Status:** Proposed

## Context

The knowledge graph needs to handle billions of nodes and edges from multiple biomedical data sources, support SPARQL queries, vector similarity search, and versioned snapshots.

## Decision

Use a layered storage approach:

- **RDBMS (PostgreSQL + Apache AGE)** — Stores entity and relationship metadata for ACID-compliant transactional access and SPARQL queries.
- **Vector index (pgvector)** — Stores node embeddings for similarity search.
- **Full-text search (PostgreSQL FTS or Elasticsearch)** — Enables rapid text search across entity names and descriptions.
- **Immutable object store** — Stores raw source data and versioned snapshots of the graph.

### Key Design Choices

- Source data is normalized into a property graph model (nodes, edges, properties).
- Each source is versioned independently; graph snapshots are assembled from specific source versions.
- Embeddings are computed offline and cached in the vector index.
- SPARQL is the primary query language; a REST wrapper provides JSON access.

## Consequences

**Positive:**
- Reliable transactional semantics for graph mutations.
- Battle-tested storage backends.
- Versioned snapshots enable reproducible queries.

**Negative:**
- Multiple storage systems to operate and tune.
- JOIN performance across RDBMS and graph layers.
- Apache AGE is a relatively young extension.

## Alternatives Considered

1. **Neo4j** — Excellent graph features, but additional operational burden and licensing for enterprise features.
2. **Amazon Neptune** — Managed, but vendor lock-in and no on-premise deployment.
3. **Pure RDBMS** — Possible for simple graphs, but awkward for deep traversal queries.
