# Search Roadmap

## Phase 5.2 — PostgreSQL Full-Text Search ✅ (Current)

- [x] FTS expression builders (`tsvector`, `tsquery`)
- [x] Ranking helpers (`ts_rank`, `ts_rank_cd`)
- [x] Highlighting helpers (`ts_headline`)
- [x] GIN index utilities
- [x] Repository integration (`execute_fts_search`)
- [x] Service layer (`search_fts`)
- [x] FTS schemas (`FullTextSearchConfig`, `FullTextSearchResponse`)
- [x] Comprehensive tests
- [x] Documentation

## Phase 5.3 — Domain Search APIs

Build domain-specific search on top of the FTS foundation:

- [ ] `GeneSearchService` — search genes by symbol, name, description
- [ ] `ProteinSearchService` — search proteins by identifier, name, function
- [ ] `VariantSearchService` — search variants by HGVS notation, gene, consequence
- [ ] `TranscriptSearchService` — search transcripts by ID, biotype, gene
- [ ] `StudySearchService` — search studies by name, description, PI
- [ ] REST endpoints for each domain search
- [ ] API documentation (OpenAPI)

## Phase 5.4 — Advanced Search Features

- [ ] Faceted search by domain attributes
- [ ] Saved searches and alerts
- [ ] Search suggestions / autocomplete
- [ ] Cross-domain search (e.g., find variant + gene + protein in one query)
- [ ] Search analytics and trending queries

## Future — OpenSearch / Elasticsearch Integration

If scale requirements exceed PostgreSQL FTS:

1. **Add OpenSearch client and index management**
2. **Asynchronous indexing via message queue**
3. **Hybrid search**: PostgreSQL for exact/simple queries, OpenSearch for complex/scale
4. **Reuse same search schemas and service interface** (swap implementations behind the repository layer)

The current architecture supports this transition: domain code depends on the search service interface, not on PostgreSQL-specific utilities.
