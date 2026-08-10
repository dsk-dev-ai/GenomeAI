# Visualization Platform

This directory documents the GenomeAI visualization platform (Phase 6).

## Status

**Phase 6.2 — Genome Browser** is the current milestone. It adds the first
concrete visualization (region parsing, viewport navigation, track rendering)
on top of the Phase 6.1 foundation.

| Milestone | Description | Status |
|-----------|-------------|--------|
| 6.1 | Visualization Foundation | ✅ Implemented |
| 6.2 | Genome Browser | ✅ Implemented |
| 6.3 | Gene / Transcript Visualization | 📋 Planned |
| 6.4 | Variant Visualization | 📋 Planned |
| 6.5 | Protein Structure Viewer | 📋 Planned |
| 6.6 | Biological Network Visualization | 📋 Planned |
| 6.7 | Scientific Charts | 📋 Planned |
| 6.8 | Integrated Research Workspace | 📋 Planned |
| 6.9 | Visualization Performance & Optimization | 📋 Planned |
| 6.10 | Visualization Testing & Documentation | 📋 Planned |

## What Phase 6.1 Provides

- A layered visualization architecture (see [Architecture](./architecture.md)).
- Strongly typed TypeScript definitions for the visualization layer.
- A reusable `VisualizationContainer` with consistent loading, empty, and error states.
- A small data abstraction (`useVisualizationData`) with request cancellation.
- A foundation demo page at `/visualization`.
- Accessibility and responsive-design conventions.

## What Phase 6.2 Provides

- An interactive Genome Browser (see [Genome Browser](./genome-browser.md)):
  one-based-inclusive coordinates, region parsing, viewport zoom/pan, a
  base-position axis, and per-track loading over the Phase 5 coordinate-search
  API.
- Pure, unit-tested genomic math modules under `apps/web/src/lib/genome/`.
- Demo integrated at `/visualization`.

## Documents

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | Component structure, data flow, and how future modules integrate |
| [Genome Browser](genome-browser.md) | Phase 6.2 Genome Browser: scope, data flow, API, a11y, tests |
| [Roadmap](roadmap.md) | Detailed phase tracking and future work |

## Technology Notes

The visualization platform is intentionally lightweight. It uses only the
existing web stack (React, TypeScript, Tailwind CSS) plus SVG layout
primitives. No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js is
used — those are introduced only when the milestone that actually requires
them arrives:

- Three.js → Phase 6.5 (protein viewer, if 3D is required)
- Cytoscape.js → Phase 6.6 (networks)
- D3.js → Phase 6.7 (scientific charts)