# Visualization Platform

This directory documents the GenomeAI visualization platform (Phase 6).

## Status

**Phase 6.9 — Integrated Research Workspace** is implemented, assembling the
Phase 6.2–6.8 visualization capabilities into one research UI at
`/visualization/workspace` around a shared genomic context, on top of the
Phase 6.10 performance work. See [Research Workspace](./workspace.md).

**Phase 6.10 — Visualization Performance & Large Dataset Handling** is
implemented, on top of the Phase 6.8 advanced scientific charts and the Phase
6.1 foundation. Phase 6.10 makes the whole platform scale to substantially
larger datasets by bounding the SVG/DOM work (deterministic downsampling,
pixel-column aggregation, heatmap block-averaging), avoiding per-render
recomputation (memoized derivations, single-pass grouping, `React.memo` marks),
and keeping the Genome Browser viewport-scoped — while preserving correctness,
accessibility, and scientific meaning. See
[Performance](./performance.md).

| Milestone | Description | Status |
|-----------|-------------|--------|
| 6.1 | Visualization Foundation | ✅ Implemented |
| 6.2 | Genome Browser | ✅ Implemented |
| 6.3 | Gene / Transcript Visualization | ✅ Implemented |
| 6.4 | Variant Visualization | ✅ Implemented |
| 6.5 | Protein Structure Viewer | ✅ Implemented |
| 6.6 | Biological Network Visualization | ✅ Implemented |
| 6.7 | Scientific Charts | ✅ Implemented |
| 6.8 | Advanced Scientific Charts | ✅ Implemented |
| 6.9 | Integrated Research Workspace | ✅ Implemented |
| 6.10 | Visualization Performance & Optimization | ✅ Implemented |
| 6.11 | Visualization Testing & Documentation | 📋 Planned |

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

## What Phase 6.3 Provides

- Gene / transcript isoform visualization (see [Gene / Transcript](./gene-transcript.md)):
  a typed domain model, pure layout geometry, and a thin adapter over the
  Phase 5 coordinate-search API — no backend changes.
- A `GeneTranscriptViewer` SVG component with gene lanes (strand arrows),
  transcript lanes (intron connectors and exon blocks), hover titles, and
  keyboard-accessible transcript selection.
- An injectable exon source: the Phase 5 API does not yet expose exons, so the
  demo uses a dev-only fixture while production callers return no exons.
- Demo integrated at `/visualization`.

## What Phase 6.4 Provides

- Variant visualization (see [Variant](./variant.md)): a typed domain model,
  pure point geometry, and a thin adapter over the Phase 5 coordinate-search
  API — no backend changes.
- A reusable `VariantTrack` component that the Genome Browser renders for
  `kind: 'variants'` tracks: coordinate-accurate point marks stacked onto
  rows when they would overlap, hover titles, and keyboard-accessible variant
  selection with a readable detail panel.
- Rich variant detail surfaced per record when the API reports it: position,
  `ref>alt`, variant `type`, quality, filter status, accession, gene, and
  description — never inferred from arbitrary strings.
- Demo integrated at `/visualization`.

## What Phase 6.5 Provides

- Protein sequence + annotation visualization (see [Protein Viewer](./protein-viewer.md)):
  a typed domain model over one-based-inclusive residue coordinates that mirror
  the genome viewer's interval semantics, pure sequence/viewport/geometry
  modules, and a thin adapter over the existing protein endpoint — no backend
  changes.
- A reusable `useProteinViewer` hook composing the shared data lifecycle with
  the residue window and feature selection, and a `ProteinViewer` component
  rendering a residue axis, stacked feature rows clipped to the visible window,
  a residue-letter lane with per-residue numbering, a residue/range input, and
  keyboard-accessible feature selection with a readable detail panel.
- Generalized base utilities shared with the genome browser
  (`intervalToPixels` → `lib/genome/geometry.ts`, `IntervalWindow` pan/zoom
  navigation, and generic row packing).
- A feature-data boundary: the backend exposes protein identity + sequence but
  not yet annotation features, so the demo uses a clearly isolated dev fixture
  routed through the same normalizers as production.
- Demo integrated at `/visualization`.

## What Phase 6.6 Provides

- Biological network visualization (see [Network Viewer](./network-viewer.md)):
  a typed relationship graph model over generic node/edge `type`s, pure
  normalization/filtering/model helpers, and a thin adapter that documents the
  future `GET /networks/{id}` contract — no backend changes.
- A **deterministic concentric layout** computed in TypeScript (degree-
  descending rings, hubs in the centre) behind a pluggable
  `LayoutStrategy`/`createLayout` seam — no Cytoscape.js dependency. See the
  design decision in [network-viewer.md](./network-viewer.md).
- A reusable `useNetworkViewer` hook composing the shared data lifecycle with
  the 2D viewport, filtering, and node/edge selection, and a `NetworkViewer`
  component rendering an interactive SVG: pan/zoom/fit, wheel zoom, drag-to-
  pan, keyboard-accessible node/edge selection, filter controls, and a
  readable detail panel.
- A network-data boundary: the backend does not yet expose a network endpoint,
  so the demo uses a clearly isolated dev fixture routed through the same
  normalizers as production.
- Demo integrated at `/visualization`.

## What Phase 6.7 Provides

- Scientific charts (see [Scientific Charts](./scientific-charts.md)): a
  typed measurement dataset model (`ExpressionPoint` / `ExpressionSeries` /
  `ExpressionDataset`), pure validation + normalization, and native scales
  (`ContinuousScale`, `CategoryScale`, `niceTicks`) — no D3.js dependency.
- A reusable `useExpressionChart` hook composing the shared data lifecycle
  with sorted samples, a raw/normalized value-field toggle, the y-domain, and
  point selection, plus responsive sizing via `useChartSize`.
- Reusable chart primitives (`ChartAxes`, `ChartLegend`, `ChartTooltip`) and an
  `ExpressionChart` SVG component: samples on the x-axis, the active value on
  the y-axis, one series (gene) per color, gridlines, axes, legend, hover
  tooltips, and keyboard-accessible point selection with a readable detail
  panel.
- An expression-data boundary: the backend does not yet expose an expression
  endpoint, so the demo uses a clearly isolated dev fixture routed through the
  same normalizers as production.
- Demo integrated at `/visualization`.

## What Phase 6.8 Provides

- Advanced scientific charts (see
  [Advanced Scientific Charts](./advanced-scientific-charts.md)): four
  reusable, interactive scientific primitives — an expression heatmap, a
  volcano plot, a genomic coverage chart, and a statistical distribution chart
  — built on the Phase 6.7 chart foundation (native scales, `ChartAxes`,
  `ChartTooltip`, responsive `useChartSize`). No D3.js or new dependencies.
- Strongly typed data models (`advancedTypes.ts`) for heatmaps, volcano plots,
  coverage bins, and distribution values, with pure validation +
  normalization + derivation + tooltip mapping per chart
  (`lib/scientific/{heatmap,volcano,coverage,distribution}.ts`).
- Shared chart data lifecycle (`useChartData`) extracted from the expression
  chart: custom-or-default loader, dataset-id reload, and the 6.1
  loading/empty/error lifecycle reused by all four hooks.
- A `ChartAxes` extension for continuous x-axes (used by the volcano plot).
- Coverage chart reuses the Phase 6.2 genome coordinate utilities
  (`createScale`, `computeTicks`, `formatBasePosition`) and viewport
  navigation (`lib/genome/viewport.ts`), so intervals and zoom/pan are shared
  with the Genome Browser rather than re-implemented.
- A thin typed adapter (`advancedApi.ts`) documenting the future
  `GET /advanced/{heatmaps|volcano|coverage|distributions}/{id}` contracts —
  no backend changes.
- An advanced-data boundary: the backend exposes none of these endpoints yet,
  so the demos use clearly isolated dev fixtures routed through the same
  normalizers as production.
- Demo integrated at `/visualization` (`AdvancedScientificDemo`).

## What Phase 6.9 Provides

- An Integrated Research Workspace (see [Research Workspace](./workspace.md))
  at `/visualization/workspace`, linked from `/visualization`, assembling the
  Phase 6.2–6.8 visualization capabilities into one research UI.
- A shared **research context** (preset loci or a custom region) that drives
  the Genome Browser and the Gene / Transcript viewer to the same genomic
  region, while the network, protein, and analysis panels reuse their existing
  hooks/components unchanged with local, predictable panel state.
- A pure `WorkspaceDataSource` seam (fixture-backed for the demo; the existing
  Phase 5 / typed adapters are the documented production path) — no backend
  changes, no new dependencies, and Phase 6.10 performance mechanisms intact.
- A responsive panel grid (single column on small screens), consistent
  loading / empty / error states through the shared `VisualizationContainer`,
  and keyboard-accessible workspace controls (labeled context select, region
  form with `role="alert"` errors, `aria-live` region announcements).
- Focused tests for workspace state, context synchronization, panel rendering,
  empty/error states, and control accessibility.

## What Phase 6.10 Provides

- Visualization performance & large-dataset handling (see
  [Performance](./performance.md)) across every Phase 6 module — no new
  dependencies, no C++/WebAssembly/WebGPU, no second rendering architecture.
- Pure deterministic downsampling/aggregation
  (`lib/scientific/downsample.ts`): stride-based `decimateItems` for points and
  scatter (volcano, expression, distribution), **peak-preserving** pixel-column
  aggregation for coverage bins, and block-average heatmap aggregation. Every
  helper is a no-op below its cap, so typical datasets render at full
  resolution.
- Per-render work reduction: memoized derived data (chromosome bins, coverage
  columns, rendered point/series sets, highlight counts, scatter samples),
  single-pass distribution grouping (`valuesByGroup`), and `React.memo` marks
  in the Network Viewer so selection changes do not recompute geometry or
  re-render every node/edge.
- The Genome Browser remains viewport-scoped: track loaders fetch only the
  settled (debounced) visible interval.
- Deterministic, non-flaky performance tests
  (`downsample.test.ts`, distribution grouping tests) and updated docs.

## Documents

| Document | Description |
|----------|-------------|
| [Architecture](architecture.md) | Component structure, data flow, and how future modules integrate |
| [Genome Browser](genome-browser.md) | Phase 6.2 Genome Browser: scope, data flow, API, a11y, tests |
| [Gene / Transcript](gene-transcript.md) | Phase 6.3 Gene / Transcript visualization: scope, data flow, API, a11y, tests |
| [Variant](variant.md) | Phase 6.4 Variant visualization: scope, data flow, API, a11y, tests |
| [Protein Viewer](protein-viewer.md) | Phase 6.5 Protein Viewer: scope, data flow, API, a11y, tests |
| [Network Viewer](network-viewer.md) | Phase 6.6 Biological Network Viewer: scope, design decision, data flow, API, a11y, tests |
| [Scientific Charts](scientific-charts.md) | Phase 6.7 Scientific Charts: scope, design decision, data flow, API, a11y, tests |
| [Advanced Scientific Charts](advanced-scientific-charts.md) | Phase 6.8 Advanced Scientific Charts: heatmap / volcano / coverage / distribution, data models, API, fixtures, a11y, tests |
| [Research Workspace](workspace.md) | Phase 6.9 Integrated Research Workspace: context, panels, state flow, API usage, fixture boundary, a11y, tests |
| [Performance](performance.md) | Phase 6.10 Visualization performance & large-dataset handling: data flow, strategies, downsampling limitations, a11y, testing |
| [Roadmap](roadmap.md) | Detailed phase tracking and future work |

## Technology Notes

The visualization platform is intentionally lightweight. It uses only the
existing web stack (React, TypeScript, Tailwind CSS) plus SVG layout
primitives. No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js is
used — those are introduced only when the milestone that actually requires
them arrives:

- Three.js → a future 3D molecular structure milestone
- Cytoscape.js → deferred: Phase 6.6 ships a deterministic pure-SVG layout
  behind the `createLayout` seam instead (see
  [network-viewer.md](./network-viewer.md)); Cytoscape.js remains available
  for later interactive/manipulation work
- D3.js → deferred: Phase 6.7 ships native scales and tick generation behind
  the `ContinuousScale` / `CategoryScale` seams instead (see
  [scientific-charts.md](./scientific-charts.md)); D3.js remains available for
  later heavy statistical charting work