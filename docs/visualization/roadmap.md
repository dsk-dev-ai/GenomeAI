# Visualization Roadmap

Tracks the Phase 6 visualization platform milestones. See
[Phase 6 of the project ROADMAP](</ROADMAP.md#phase-6--visualization-platform>) for
the authoritative milestone list.

## Current Milestone: 6.11 — Visualization Testing & Documentation ✅

A stabilization + docs pass over the whole Phase 6 platform, on top of 6.10.

Delivered:

- **Coverage audit** across every Phase 6 module (foundation, genome,
  scientific, network, protein, workspace): mapped tested vs untested modules,
  components, and a11y semantics; identified `visualizationModules.ts` and
  `useChartSize.ts` as untested modules and the chart primitives + workspace
  panels as untested components.
- **Latent bug fixed by the audit**: `panViewport` produced a start below base 1
  when a window wider than the contig panned right; it now clamps like
  `zoomViewport` (`lib/genome/viewport.ts`).
- **Data-contract tests** (`visualizationModules.test.ts`): catalog ids,
  titles, milestones, fresh-copy semantics, delay/failure/abort behavior.
- **Responsive sizing tests** (`useChartSize.test.tsx`): default/custom
  fallbacks, resize observation, zero-measurement guard, unmount cleanup.
- **Edge/correctness expansion** across the suite: downsampling boundaries
  (exact caps, non-positive limits, ragged blocks, NaN/Infinity),
  genome coordinate + viewport boundaries (invalid regions, overflow, pan/zoom
  clamps), Genome Browser lifecycle (debounce collapse, in-flight abort,
  navigation clamps), API contracts (paginated coordinate search, page_size,
  abort between pages, malformed payloads), track layout (stacking,
  tie-break ordering, empty views), statistics (single-element summaries,
  quantile interpolation, whiskers/outliers), and data-lifecycle races
  (stale errors ignored, selection cleared on reload, data cleared during
  refetch).
- **Focused component + a11y tests**: `ChartAxes`, `ChartLegend`,
  `ChartTooltip` (labels, list semantics, tooltip clamping), and the workspace
  panels (loading state, error + retry, whole-dataset panels independent of
  context changes).
- **Reconciled documentation**: README, architecture tree, roadmap test
  counts, module out-of-scope references, and the module catalog comment now
  match the shipped platform; new [Testing](testing.md) guide.
- Web suite grows from 725 to **813 tests** (68 files) — deterministic, no
  timing-based benchmarks; full validation green.

Constraints honored:

- No new visualization features, architecture redesign, or Phase 6.12 work;
  no C++/WebAssembly/WebGPU/Three.js/Cytoscape.js/D3.js; no new runtime
  dependencies; Phase 5 untouched
- No tests deleted, weakened, or skipped; additions are behavior-oriented
  (never implementation-detail fakes)
- Docs claims are accurate against the current repo (test counts, milestone
  status, component tree)

## Previous milestones

### 6.9 — Integrated Research Workspace ✅

Implemented on top of 6.8 (and the Phase 6.10 performance work).

Delivered:

- A dedicated workspace route `/visualization/workspace` (linked from
  `/visualization`) assembling the Phase 6.2–6.8 capabilities into one research
  UI
- A shared research context (preset TP53 / BRCA1 loci, or a custom region)
  that drives the Genome Browser and the Gene / Transcript viewer to the same
  genomic region (`lib/workspace/researchContext.ts`)
- A pure `WorkspaceDataSource` seam (`lib/workspace/dataSources.ts`) with a
  fixture-backed demo provider (`components/workspace/fixtureDataSources.ts`)
  routed through the same normalizers as production; the existing Phase 5 /
  typed adapters are the documented production path — no backend changes
- Thin panels that reuse the shipped components/hooks unchanged (Genome
  Browser, Gene / Transcript viewer, Network Viewer, Protein Viewer, and the
  Phase 6.7/6.8 charts); region-driven panels are remounted on context change
  while whole-dataset panels keep local, predictable state
- A responsive panel grid, consistent loading / empty / error states via the
  shared `VisualizationContainer`, and keyboard-accessible controls (labeled
  context select, region form with `role="alert"` errors, `aria-live` region
  announcements)
- Tests (30 workspace tests) and docs (see
  [Research Workspace](workspace.md))

Constraints honored:

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, D3.js, or a second
  rendering architecture; no new runtime dependencies
- Existing visualization components are reused, not rewritten; Phase 6.10
  performance mechanisms remain intact (full datasets stay the source of truth)
- The 6.1 `useVisualizationData` lifecycle remains the data authority
- No invented backend endpoints; the fixture boundary is documented
- Phase 5 search untouched

## Previous milestones

### 6.10 — Visualization Performance & Large Dataset Handling ✅

Implemented on top of 6.8.

Delivered:

- Performance analysis across the Phase 6 platform identifying the real hot
  spots before any change (per-mark geometry on every network render, one SVG
  node per cell/point/bin, O(groups × values) distribution statistics, per-
  render path/filter rebuilds) — see [Performance](performance.md)
- Pure deterministic downsampling (`lib/scientific/downsample.ts`):
  `decimateItems` (stride sample, first/last preserved, hard bound),
  `coverageColumns` (peak-preserving pixel-column aggregation for coverage),
  `aggregateHeatmap` (block-average for oversized matrices) — all no-ops below
  their caps so typical datasets render unchanged
- Component bounds: volcano (`MAX_RENDERED_POINTS = 2000`), expression chart
  (`MAX_SERIES_POINTS = 1000`), distribution scatter (`MAX_SCATTER_POINTS_PER_GROUP
  = 1000`, outliers always kept), coverage (`MAX_COVERAGE_COLUMNS = 2000`),
  heatmap (`MAX_HEATMAP_ROWS/COLS = 150` with a "(block-summarized)" note)
- Per-render work reduction: memoized chromosome bins / coverage columns /
  rendered point+series sets / highlight counts / scatter samples; single-pass
  `valuesByGroup` grouping in `useDistributionChart` (O(values) not
  O(groups × values)); `React.memo` Network Viewer marks with primitive props so
  selection/filter changes skip most re-renders
- Genome Browser stays viewport-scoped (per-track loaders fetch only the
  settled debounced interval)
- Full data remains the source of truth for tooltips/selection/summaries —
  downsampling only affects the marks drawn, never the interaction
- Deterministic, non-flaky performance tests (`downsample.test.ts`, distribution
  grouping tests) and docs (see [Performance](performance.md))

Constraints honored:

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, D3.js, or a second
  rendering architecture; no new runtime dependencies
- No new cache abstraction; memoization is scoped to justified derivations and
  the existing `useVisualizationData` lifecycle remains the data authority
- Downsampling is documented, deterministic, and never silently discards signal
  (peaks, outliers, block means preserved); accessibility (labels, keyboard,
  aria-pressed, focus rings) is unchanged for decimated marks
- Phase 5 search untouched

## Previous milestones

### 6.8 — Advanced Scientific Charts ✅

Implemented on top of 6.7.

Delivered:

- Strongly typed data models (`lib/scientific/advancedTypes.ts`) — heatmap
  matrix (`HeatmapDataset`), volcano points (`VolcanoPoint`/`VolcanoDataset`),
  coverage bins (`CoverageBin`/`CoverageDataset`), distribution values
  (`DistributionValue`/`DistributionDataset`); generic and opaque about the
  biological *meaning* of values
- Pure per-chart transformation modules (`lib/scientific/heatmap.ts`,
  `volcano.ts`, `coverage.ts`, `distribution.ts`) — typed validation, canonical
  normalization (deterministic ordering, dedupe, invalid drops), domains,
  color scale, highlight thresholds, and tooltip mapping
- Pure statistics (`lib/scientific/statistics.ts`) — sorted sample, R-7
  quantiles, `summarize`, box-plot whiskers; kept separate from rendering
- Shared chart data lifecycle (`lib/scientific/useChartData.ts`) — extracted
  from `useExpressionChart` and reused by all four advanced hooks (custom /
  default loader, dataset-id reload, 6.1 loading/empty/error lifecycle)
- Thin typed adapter (`lib/scientific/advancedApi.ts`) documenting the future
  `GET /advanced/{heatmaps|volcano|coverage|distributions}/{id}` contracts
  (no backend changes)
- View-model hooks (`useHeatmap`, `useVolcanoPlot`, `useCoverageChart`,
  `useDistributionChart`) — load lifecycle, derived domains/groups/statistics,
  selection; the coverage hook drives a Phase 6.2 `GenomeViewport`
- Components (`components/scientific/`): `Heatmap` (diverging color grid with
  missing-value cells), `VolcanoPlot` (effect-size vs significance, threshold
  lines, highlighted points), `CoverageChart` (genomic area chart reusing
  `lib/genome` coordinates + viewport, zoom/pan/reset + chromosome controls),
  `DistributionChart` (box plot with deterministic jitter and outliers);
  `ChartAxes` extended with a continuous x-axis
- Demo integrated at `/visualization` (`AdvancedScientificDemo` uses the dev
  fixtures)
- Tests (282 across the scientific modules at delivery; 343 across the
  scientific modules today) and docs (see
  [Advanced Scientific Charts](advanced-scientific-charts.md))

Constraints honored:

- The charts never assert biological validity or hard-code gene / disease /
  database knowledge; values stay opaque finite numbers, and the volcano plot
  treats `significance` as whatever finite score the caller provides (no
  p-value assumptions)
- Backend advanced endpoints are not yet exposed, so the demos use clearly
  isolated dev fixtures routed through the same normalizers as production
- The coverage chart reuses the Phase 6.2 genome coordinate types/utilities and
  viewport instead of duplicating interval logic
- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js; no new
  runtime dependencies
- Phase 5 search untouched

## Previous milestones

### 6.7 — Scientific Charts ✅

Implemented on top of 6.6.

Delivered:

- Typed measurement data model (`lib/scientific/types.ts`) —
  `ExpressionPoint`, `ExpressionSeries`, `ExpressionDataset`, `PointKey`;
  generic enough for later chart types (coverage, statistical, QC)
- Pure validation + normalization (`lib/scientific/expression.ts`) —
  typed error reports, canonical ordering, dedupe by entity + sample,
  sample/domain derivation, zero-anchored/padded y-domains
- Native scales (`lib/scientific/scale.ts`) — invertible continuous scale,
  category scale, 1/2/5 × 10^n `niceTicks`, deterministic label stepping; no
  D3.js (see
  [Scientific Charts](scientific-charts.md#design-decision-native-scales-no-d3js))
- Pure chart geometry (`lib/scientific/geometry.ts`) — margins/plot area,
  deterministic colorblind-aware palette
- Tooltip mapping (`lib/scientific/tooltip.ts`) — shared labelled rows for the
  hover tooltip and the accessible detail panel
- Thin typed adapter (`lib/scientific/api.ts`) documenting the future
  `GET /expression/datasets/{id}` contract (no backend changes)
- `useExpressionChart` hook — load lifecycle (via the shared
  `useVisualizationData`) + sorted samples + value-field toggle + y-domain +
  point selection; `useChartSize` for responsive widths
- Reusable chart primitives (`components/scientific/`) — `ChartAxes`,
  `ChartLegend`, `ChartTooltip`, and the `ExpressionChart` SVG component
  (gridlines, axes, legend, hover tooltips, keyboard-accessible point
  selection, detail panel)
- Demo integrated at `/visualization` (`ScientificDemo` uses the dev fixture)
- Tests (85 across the scientific modules at delivery; 343 across the
  scientific modules today) and docs (see
  [Scientific Charts](scientific-charts.md))

Constraints honored:

- The chart layer never asserts biological validity or hard-codes gene /
  disease / database knowledge; expression values stay opaque finite numbers
- Backend expression endpoints are not yet exposed, so the demo uses a clearly
  isolated dev fixture routed through the same normalizers as production
- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js; no new
  runtime dependencies
- Phase 5 search untouched

### 6.6 — Biological Network Viewer ✅

Delivered:

- Typed domain model (`lib/network/types.ts`) — `Graph`, `GraphNode`,
  `GraphEdge`, `GraphLayout`, `NetworkViewport`, `GraphFilter`,
  `GraphViewerState`; node/edge `type`s are opaque strings so the viewer is not
  hard-wired to one annotation source
- Pure model helpers (`lib/network/model.ts`) — lookups, degree, available
  node/edge types, graph validation
- Pure normalization (`lib/network/normalize.ts`) — dedupe ids, drop
  self-loops and dangling edges, deterministic ordering
- Pure filtering (`lib/network/filter.ts`) — node/edge-type filters with
  no-dangling-edge guarantees
- Pure deterministic layout (`lib/network/layout.ts`) — concentric rings by
  degree (hubs in the centre) behind a pluggable `createLayout` /
  `LayoutStrategy` seam; no Cytoscape.js (see
  [Network Viewer](network-viewer.md#design-decision-deterministic-pure-svg-layout-no-cytoscapejs))
- Pure 2D viewport (`lib/network/viewport.ts`) — identity/fit viewports,
  clamped pan/zoom, projection; `ZOOM_FACTOR` mirrors the genome/protein
  viewers
- Pure render geometry (`lib/network/geometry.ts`) — SVG constants, edge
  endpoints inset to node edges, node hit boxes
- Presentation helpers (`lib/network/labels.ts`) — type colours, display +
  accessible labels, detail-panel rows
- Thin typed adapter (`lib/network/api.ts`) documenting the future
  `GET /networks/{id}` contract (no backend changes)
- `useNetworkViewer` hook — load lifecycle (via the shared
  `useVisualizationData`) + deterministic layout + viewport + filter +
  node/edge selection
- `NetworkViewer` SVG component — pan/zoom/fit, wheel zoom, drag-to-pan,
  keyboard-accessible node/edge selection, filter controls, detail panel
- Demo integrated at `/visualization` (`NetworkDemo` uses the dev fixture)
- Tests (98 across the network modules) and docs (see
  [Network Viewer](network-viewer.md))

Constraints honored:

- The viewer is a visualization layer, never a source of scientific
  relationship data; node/edge `type`s are never inferred from labels
- Layout is deterministic ("same input, stable output") with no PRNG
- Backend network endpoints are not yet exposed, so the demo uses a clearly
  isolated dev fixture routed through the same normalizers as production
- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js; no new
  runtime dependencies
- Phase 5 search untouched

### 6.5 — Protein Viewer ✅

Implemented on branch `feat/visualization-protein-viewer`, on top of 6.4.

Delivered:

- Typed domain model (`lib/protein/types.ts`) — `Protein`, `ProteinFeature`,
  `ProteinFeatureType`, `ProteinViewport`, `ProteinResidue`, `ProteinViewerState`
- Pure sequence helpers (`lib/protein/sequence.ts`) — 1-based residue indexing,
  validators, and window slicing
- Pure viewport math (`lib/protein/viewport.ts`) — opening window, clamped
  zoom/pan/navigate, and typed region parsing, reusing the shared
  `IntervalWindow` utilities so protein navigation cannot drift from genomic
  navigation
- Pure geometry (`lib/protein/geometry.ts`) — residue/feature pixel mapping and
  axis-critical ticks via the shared genome scale, stable row packing
- Feature presentation helpers (`lib/protein/features.ts`) — type
  normalization, colours, labels, accessible labels, detail rows
- Thin typed adapter (`lib/protein/api.ts`) over the existing protein endpoint
  (`GET /proteins/{id}`, no backend changes) with injectable feature source
- `useProteinViewer` hook — protein load lifecycle (via the shared
  `useVisualizationData`) + viewport + feature selection
- `ProteinViewer` SVG component — residue axis, stacked feature rows clipped to
  the window, residue-letter lane with per-residue numbering, region input,
  and keyboard-accessible feature selection with a detail panel
- Generalized base utilities: `intervalToPixels` → `lib/genome/geometry.ts`,
  `panViewport`/`zoomViewport` → `IntervalWindow` (shared with the protein
  viewport), and generic row packing (`layoutRows`)
- Demo integrated at `/visualization` (`ProteinDemo` uses the dev fixture)
- Tests (104 across the protein modules) and docs (see
  [Protein Viewer](protein-viewer.md))

Constraints honored:

- The viewer is the sequence/annotation foundation, NOT a 3D structure renderer;
  3D work stays on a future milestone that requires it
- Feature `type` is carried as opaque text and normalized only for presentation,
  never inferred from labels or sequence
- Backend annotation features are not yet exposed, so the demo uses a clearly
  isolated dev fixture routed through the same normalizers as production
  (see [Protein Viewer](protein-viewer.md#feature-data-boundary))
- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js
- Phase 5 search untouched; no new runtime dependencies

### 6.4 — Variant Visualization ✅

Implemented on branch `feat/visualization-variant`, on top of 6.3.

Delivered:

- Typed domain model (`lib/genome/variant.ts`) — `Variant` (reusing the
  existing `VariantFeature` type), normalization from raw search items,
  validation, and display helpers (label, accessible label, detail lines)
- Pure point geometry (`lib/genome/variantGeometry.ts`) — in-viewport filtering
  for single positions, pixel mapping via the shared scale, deterministic row
  stacking for dense/identical marks, lane height
- Thin typed adapter (`lib/genome/variantApi.ts`) over the Phase 5
  coordinate-search API (no backend changes)
- `VariantTrack` SVG component — coordinate-accurate point marks, hover titles,
  keyboard-accessible selection (`role="button"`, Enter/Space, `aria-pressed`),
  and a readable detail panel
- The Genome Browser now routes `kind: 'variants'` tracks through the reusable
  `VariantTrack` (no inline variant branch)
- Enriched `VariantFeature` / `toVariantFeature` with `variantId`,
  `variantType`, `quality`, `filterStatus`, `geneId`, `description`
- Demo integrated at `/visualization` (variants track uses `fetchVariants`)
- Tests and docs (see [Variant](variant.md))

Constraints honored:

- Variant `type` is carried as opaque text and never inferred from arbitrary
  strings or `ref`/`alt`; only API-reported fields are displayed
- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js
- Phase 5 search untouched; no new runtime dependencies

### 6.3 — Gene / Transcript Visualization ✅

Implemented on branch `feat/visualization-gene-transcript`, on top of 6.2.

Delivered:

- Typed domain model (`lib/genome/geneTranscript.ts`) — `Gene`, `GeneTranscript`,
  `GeneExon`, normalization from raw search items, validators, transcript
  sorting, and gene grouping
- Pure geometry module (`lib/genome/geneTranscriptGeometry.ts`) — exon,
  transcript, and gene spans, lane layout, height, viewport clipping
- Thin typed adapter (`lib/genome/geneTranscriptApi.ts`) over the Phase 5
  coordinate-search API (no backend changes) with an injectable exon source
- `GeneTranscriptViewer` SVG component — gene lane with strand arrow, transcript
  lanes with intron connector lines and exon blocks, hover titles, and
  keyboard-accessible transcript selection (`role="button"`, Enter/Space)
- Demo integrated at `/visualization` (`GeneTranscriptDemo`)
- Tests and docs (see [Gene / Transcript](gene-transcript.md))

Exon boundary:

- The Phase 5 API currently returns genes and transcripts but no exon structure.
  The frontend model supports exons via an injectable `ExonSource`; a dev-only
  fixture provides representative TP53 / BRCA1-like data. This is documented in
  [Gene / Transcript](gene-transcript.md#exon-data-boundary).

Constraints honored:

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js
- Phase 5 search untouched; no new runtime dependencies

### 6.2 — Genome Browser ✅

Implemented on branch `feat/visualization-genome-browser`, on top of 6.1.

Delivered:

- One-based-inclusive genomic coordinate model (`lib/genome/types.ts`)
- Chromosome normalization plus region parsing with typed error codes
- Pure viewport math (clamped zoom/pan), pixel geometry, axis ticks
- Minimal track architecture (row packing, in-viewport clipping)
- `useGenomeBrowser` hook — debounced per-track region fetch through the
  6.1 `useVisualizationData` lifecycle
- `GenomeBrowser` SVG component with navigation controls and region input
- Thin typed adapter over the Phase 5 coordinate-search API (no backend
  changes)
- Tests and docs (see [Genome Browser](genome-browser.md))

Constraints honored:

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js
- Phase 5 search untouched; no new runtime dependencies

### 6.1 — Visualization Foundation ✅

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
| 6.12 | Molecular Structure Viewer (3D) | 3D protein structures; Three.js only if 3D is truly required |