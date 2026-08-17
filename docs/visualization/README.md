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

**Phase 6.11 — Visualization Testing & Documentation** is implemented: a
testing and documentation pass over the whole Phase 6 platform. It audits
coverage across every Phase 6 module, adds behavior/correctness/edge tests
where they were thin (foundation, genome, scientific, and workspace modules),
fixes latent bugs the audit uncovered (viewport pan clamping), adds focused
accessibility and component tests for previously untested chart primitives and
workspace panels, and reconciles the docs with the shipped platform. See
[Testing](./testing.md) and the [Roadmap](./roadmap.md).

**Phase 6.12 — Molecular Structure Viewer** is implemented: a first
production-quality 3D molecular structure viewer. It renders structures
through Three.js behind a pure `MolecularViewer` seam (cartoon / ribbon,
ball-and-stick, and space-filling representations), with orbit/zoom/pan
camera controls, reset/fit framing, show/hide, a labelled select and
`aria-pressed` controls, and full GPU/geometry disposal. The backend exposes
no structure endpoint yet, so the demo renders a clearly isolated synthetic
development fixture through the same typed normalizer the future structure
adapter will use. See [Molecular Structure](./molecular-structure.md).

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
| 6.11 | Visualization Testing & Documentation | ✅ Implemented |
| 6.12 | Molecular Structure Viewer | ✅ Implemented |

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

## What Phase 6.11 Provides

- A **coverage audit** of every Phase 6 module (foundation, genome, scientific,
  network, protein, workspace) identifying untested modules, untested
  components, and a11y gaps.
- **Behavior/correctness/edge tests** added across the suite: data-contract
  tests for the visualization-module catalog (`visualizationModules.test.ts`),
  responsive sizing (`useChartSize.test.tsx`), downsampling/aggregation edge
  cases, genome coordinate + viewport boundaries, Genome Browser track/region
  lifecycle (debounce, stale-abort), coordinate-search and advanced API
  contracts (pagination, malformed input, abort), track layout stacking,
  statistics (quantiles, whiskers), and data-lifecycle races (stale errors,
  selection clearing).
- **Focused component and accessibility tests** for the previously untested
  chart primitives (`ChartAxes`, `ChartLegend`, `ChartTooltip`) and workspace
  panels (loading/error states, context-change independence, `aria-live` /
  `role` semantics).
- **A latent bug fixed by the audit**: `panViewport` could produce a start
  below base 1 when a window wider than the contig panned right; it now clamps
  like `zoomViewport`.
- **Reconciled documentation**: architecture and roadmap now match the shipped
  platform (accurate tree, milestone status, test counts), plus a
  [Testing](./testing.md) guide describing coverage and how to run the suite.
- The web suite grows from 725 to 813 tests with no flaky or timing-based
  benchmarks.

## What Phase 6.12 Provides

- A **Molecular Structure Viewer** (see
  [Molecular Structure](./molecular-structure.md)): interactive 3D rendering of
  a molecular structure — orbit, zoom, and pan the camera; switch between
  cartoon / ribbon, ball-and-stick, and space-filling representations; reset
  or fit the view; and show/hide the structure.
- A **typed canonical structure model** (`lib/molecular/types.ts`) with
  angstrom coordinates, 1-based atom serials and residue numbers (mirroring the
  Phase 6.5 protein residue convention), chains/residues/bonds, and a pure
  validator (`lib/molecular/validate.ts`) that reports structural issues
  (missing ids, dangling bonds, duplicate serials, non-finite coordinates)
  instead of silently rendering malformed data.
- Pure, unit-tested geometry (`lib/molecular/geometry.ts`): CPK element
  presentation, bounding boxes, centroids, camera framing, backbone traces,
  and structure summaries — shared by the viewer and its tests.
- **Three.js** behind a pure seam: the React layer talks only to a
  `MolecularViewer` interface (`lib/molecular/render/types.ts`); the WebGL
  implementation (`render/threeViewer.ts`) owns the scene, camera, orbit
  controls, resize handling, and full disposal, with an injectable renderer so
  tests never need a GPU. The object-graph builder
  (`render/representationBuilder.ts`) creates only Three.js objects and is
  unit-tested in jsdom.
- A **data boundary**: the backend exposes no structure endpoint yet, so
  `lib/molecular/api.ts` documents the future `GET /structures/{id}` contract
  and normalizes whatever a source returns via `toStructure`; the demo renders
  a clearly isolated, deterministically generated synthetic development
  fixture routed through the same normalizer as production.
- A reusable `useMolecularStructureViewer` hook and `MolecularStructureViewer`
  component (`/visualization/molecular-structure`), with an accessible canvas
  (`role="img"` + `aria-label`), labelled controls, a live structure summary,
  and the shared `VisualizationContainer` lifecycle.
- 84 new tests across the molecular module (validation, geometry,
  representations, API normalization, hook lifecycle, component lifecycle with
  an injected fake viewer, and Three.js lifecycle with a fake renderer), plus
  the catalog entry and data-contract updates for the module catalog.

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
| [Testing](testing.md) | Phase 6.11 Testing & documentation pass: coverage map, test conventions, and how to run the suite |
| [Molecular Structure](molecular-structure.md) | Phase 6.12 Molecular Structure Viewer: 3D representations, Three.js design decision, data model, API, fixture boundary, a11y, tests |
| [Roadmap](roadmap.md) | Detailed phase tracking and future work |

## Technology Notes

The visualization platform is intentionally lightweight. It uses the existing
web stack (React, TypeScript, Tailwind CSS) plus SVG layout primitives, and —
for Phase 6.12's 3D molecular structure milestone only — **Three.js** (runtime
`three` + `@types/three`). No C++, WebAssembly, WebGPU, Cytoscape.js, or D3.js
is used; those remain deferred until a milestone actually requires them:

- Three.js → Phase 6.12 uses Three.js directly (not a molecular-viewer
  library such as NGL or bio3d-viewer) behind a pure `MolecularViewer` seam;
  see [molecular-structure.md](./molecular-structure.md) for the design
  decision
- Cytoscape.js → deferred: Phase 6.6 ships a deterministic pure-SVG layout
  behind the `createLayout` seam instead (see
  [network-viewer.md](./network-viewer.md)); Cytoscape.js remains available
  for later interactive/manipulation work
- D3.js → deferred: Phase 6.7 ships native scales and tick generation behind
  the `ContinuousScale` / `CategoryScale` seams instead (see
  [scientific-charts.md](./scientific-charts.md)); D3.js remains available for
  later heavy statistical charting work