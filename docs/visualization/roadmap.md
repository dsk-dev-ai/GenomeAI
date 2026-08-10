# Visualization Roadmap

Tracks the Phase 6 visualization platform milestones. See
[Phase 6 of the project ROADMAP](</ROADMAP.md#phase-6--visualization-platform>) for
the authoritative milestone list.

## Current Milestone: 6.4 — Variant Visualization ✅

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

## Previous milestones

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

## Previous milestones

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
| 6.5 | Protein Structure Viewer | 3D; Three.js only if 3D is truly required |
| 6.6 | Biological Network Visualization | Interaction graphs; Cytoscape.js |
| 6.7 | Scientific Charts | Trend/QC plots; D3-based |
| 6.8 | Integrated Research Workspace | Assembles 6.4–6.7 into a UI |
| 6.9 | Visualization Performance & Optimization | Virtualization / density rendering for large data |
| 6.10 | Visualization Testing & Documentation | Stabilization + docs pass |