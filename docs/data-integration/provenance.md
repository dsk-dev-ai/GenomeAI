# Provenance & Reproducibility

External scientific records must be traceable: where a fact came from, which
version of the source it reflects, when it was retrieved, and whether the
bytes are still the same.

## Raw-data boundary

`RawRecord` (`integration/raw_data.py`) is captured **before** normalization:

| Field | Purpose |
| --- | --- |
| `source` | stable source id (`genomeai-reference`, future `ncbi-gene`, …) |
| `source_id` | external record identifier |
| `source_version` | source-reported release, `None` when unknown — never invented |
| `retrieved_at` | ISO-8601 fetch timestamp (filled by the fetch layer) |
| `payload` / `payload_ref` | raw bytes/JSON now; object-storage reference later |
| `payload_sha256` | checksum via `with_checksum()` |

Checksums are deterministic: `checksum_json` canonicalizes key order before
hashing, so identical logical payloads hash identically.

## Provenance model

`ProvenanceRecord` (domain) persists into the `provenance` table
(`integration/models/provenance.py`):

- `source_id` + `source_record_id` — what was fetched
- `source_version` — release/version reported by the connector
- `retrieved_at` — when fetched; `ingested_at` — DB default at insert
- `checksum` — SHA-256 of the raw payload
- `source_url` — public reference URL for humans

GenomeAI does not fabricate releases: if a connector cannot report a version,
the column stays `NULL`.

## External identifiers

Cross-database identity is one concept in one table
(`external_identifiers`), enabling mappings like:

```
Gene (genomeai_entity_id)
├── NCBI Gene ID      (source=ncbi,     external_id=7157)
├── Ensembl Gene ID   (source=ensembl,  external_id=ENSG00000141510)
└── HGNC ID           (source=hgnc,     external_id=11998)
```

Uniqueness contract on `(source_id, external_id, entity_type, namespace)`:

- Two partial unique indexes avoid Postgres's "NULLs are distinct" pitfall:
  - namespace IS NULL → `uq_external_identifier`
  - namespace IS NOT NULL → `uq_external_identifier_ns`
- The repository maps SQLSTATE 23505 to `DuplicateExternalIdentifierError`
  (HTTP 409) instead of silently overwriting.

## Job-level traceability

Every ingestion run is an `IngestionJob`: pending → running →
succeeded/failed/cancelled, with timestamps and record counts. Failed jobs
require a non-empty `error_message`; optional structured `error_detail`
carries machine-readable context (status codes, counts) without credentials
or raw payloads.

## Guarantees

1. Every imported fact can be traced back to source + record id + version.
2. Payload integrity can be verified via SHA-256 at any time.
3. Identifier uniqueness is enforced by the database, not conventions.
4. No legal terms or releases are asserted by GenomeAI itself; both are
   connector-supplied data.
