# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Sponsors funding (`.github/FUNDING.yml`)
- Comprehensive README with architecture, features, data sources, and quick start
- Public API integration roadmap (37+ free biomedical databases)

### Changed
- Updated ROADMAP.md with delivered work, API integration plan, cost-effective AI strategy
- Updated ARCHITECTURE.md with current implementation status
- Updated CONTRIBUTING.md with development setup instructions
- Updated ADR 001 to reflect actual DAG engine implementation

---

## Release History

- No stable releases yet. See [ROADMAP.md](ROADMAP.md) for upcoming milestones.

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
