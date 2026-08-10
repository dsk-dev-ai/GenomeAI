# External Data & API

This area governs how GenomeAI integrates external scientific sources. It is the controlling reference for everything built in Phases 4–9.

## Rule

> GenomeAI must never make the frontend depend directly on 20–30 external APIs.

```
External sources → connectors/ingestion → normalized GenomeAI data → GenomeAI API → Web/AI
```

## Contents

- [MASTER_PLAN.md](./MASTER_PLAN.md) — the official GenomeAI External Data & API Master Plan: architecture, tiers, connectors, storage, ingestion, accuracy, and phase integration order.
