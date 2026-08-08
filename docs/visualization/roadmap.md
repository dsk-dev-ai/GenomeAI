# Visualization Roadmap

Tracks the Phase 6 visualization platform milestones. See
[Phase 6 of the project ROADMAP](</ROADMAP.md#phase-6--visualization-platform>) for
the authoritative milestone list.

## Current Milestone: 6.1 — Visualization Foundation ✅

Implemented on branch `feat/visualization-foundation`.

Delivered:

- Layered visualization architecture (see [Architecture](architecture.md))
- Visualization `types.ts` — identifiers, status, metadata, dimensions, error,
  and a discriminated `VisualizationDataState<T>`
- `useVisualizationData` hook with loading/success/empty/error states, stale
  request protection, `AbortSignal` cancellation, and `refetch`
- `VisualizationContainer` + `VisualizationLoading`, `VisualizationEmpty`,
  `VisualizationErrorState` with accessibility semantics
- Foundation demo route `/visualization`
- Vitest + Testing Library harness in `apps/web`
- `docs/visualization` documentation

Constraints honored:

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js
- No speculative dependencies; D3.js/Three.js/Cytoscape.js deferred to the
  milestones that actually require them
- Phase 5 search untouched

## Future milestones

| # | Milestone | Notes |
|---|-----------|-------|
| 6.2 | Genome Browser | Dense region track rendering; likely D3-based |
| 6.3 | Gene / Transcript Visualization | Isoform structure, expression; D3-based |
| 6.4 | Variant Visualization | Variant tables + tracks; D3-based |
| 6.5 | Protein Structure Viewer | 3D; Three.js only if 3D is truly required |
| 6.6 | Biological Network Visualization | Interaction graphs; Cytoscape.js |
| 6.7 | Scientific Charts | Trend/QC plots; D3-based |
| 6.8 | Integrated Research Workspace | Assembles 6.2–6.7 into a UI |
| 6.9 | Visualization Performance & Optimization | Virtualization for large data |
| 6.10 | Visualization Testing & Documentation | Stabilization + docs pass |