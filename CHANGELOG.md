# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-29

### Added
- Public **Live Demo deployment**: release-triggered GitHub Actions workflow
  (`.github/workflows/release-deploy.yml`) deploying the FastAPI backend to
  Render and the Next.js frontend to Vercel, with health checks and UI/API
  smoke tests; `Dockerfile.api`, `render.yaml`, and deployment docs
  (`docs/deployment/architecture.md`, `docs/deployment/releases.md`)
- `Live Demo` link and website field in the README/repository
- GitHub Sponsors funding (`.github/FUNDING.yml`)
- Comprehensive README with architecture, features, data sources, and quick start
- 18 real external-data connectors (NCBI, Ensembl VEP, UniProt, ClinVar, gnomAD,
  PDB, AlphaFold, ChEMBL, PubChem, Reactome, KEGG, STRING, OpenTargets, Monarch,
  Disease Ontology, DGIdb, Europe PMC, Semantic Scholar)
- 8 AI analysis services: gene, variant, protein, drug, pathway, disease,
  literature, and multi-domain report
- Search engine (full-text, domain search, query DSL)
- AI analysis via gemini-3.6-flash with graceful fallbacks to basic analysis

### Changed
- AI gene/protein analysis: raised `max_tokens` to 4096, salvages
  markdown-fenced and truncated JSON, and falls back honestly to basic
  analysis (source `ncbi`) when unusable
- Frontend deploy in the release workflow now uses the Vercel REST API instead
  of `amondnet/vercel-action` (the action is incompatible with current Vercel
  CLI); removed the redundant `deploy.yml` workflow (Vercel GitHub integration
  already deploys main pushes and PR previews)
- Updated ROADMAP.md with delivered work and current state
- Updated ARCHITECTURE.md with current implementation status
- Updated CONTRIBUTING.md with development setup instructions
- Updated ADR 001 to reflect actual DAG engine implementation

## Unreleased

### Planned
- Knowledge graph (gene-disease-drug-protein associations)
- More AI providers (OpenAI, Anthropic, Groq, Mistral)
- Plugin SDK and marketplace
- Authentication & multi-user organizations

## Delivered Milestones

### Phase 7 — Workflow Engine (Phases 7.1–7.6)

| Phase | Description | PRs |
|-------|-------------|-----|
| 7.1 | Workflow Foundation: definitions, steps, dependencies, DAG validation, run/step state models, persistence, admin API | #42 |
| 7.2 | DAG Execution Engine: deterministic sequential in-process execution | #43 |
| 7.3 | Workflow Scheduler: application-level due-run detection, cron schedules, timezone handling | #44 |
| 7.4 | Queue & Worker: background execution via Redis queue, claim/release, graceful shutdown | #45 |
| 7.5 | Retry & Failure: failure classification, retry policies, backoff, attempt tracking, manual retry | #46 |
| 7.6 | Parallel DAG Execution: concurrent independent steps, configurable max_concurrency, structured concurrency | #47 |

### Phase 6 — Visualization Platform

| Feature | PRs |
|---------|-----|
| Genome browser, gene/transcript viewer, variant track | #28–#33 |
| Protein viewer, network viewer, scientific charts | #34–#37 |
| Molecular structure viewer, research workspace | #38–#40 |

### Phase 0–1 — Foundation & Core Platform

| Feature | PRs |
|---------|-----|
| Repository foundation, docs, governance, CI/CD | #1–#6 |
| Biological domain models (Genome, Sample, Gene, Variant, Transcript) | #7–#22 |
| REST API v1 with CRUD endpoints | #7–#22 |

### Data Integration

| Feature | PRs |
|---------|-----|
| Data integration foundation (sources, fetchers, connectors) | #41 |
