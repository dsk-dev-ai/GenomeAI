# Visualization Performance & Large Dataset Handling

This document describes how the GenomeAI visualization platform (Phase 6)
stays responsive on large datasets. It covers the data flow, the measured hot
spots, the strategies used to bound work, and their limitations.

## Architecture and data flow

The platform is a React/SVG stack — no C++, WebAssembly, WebGPU, or a second
rendering architecture. Every visualization follows the same layered flow:

1. **Load once per dataset id.** `useVisualizationData` owns the
   loading / empty / success / error lifecycle with `AbortSignal` cancellation
   and stale-response protection. The scientific chart hooks wrap it in
   `useChartData`; network / protein / genome hooks use it directly.
2. **Derive pure view models.** Pure modules under `lib/scientific`,
   `lib/network`, `lib/genome`, and `lib/protein` turn raw data into render-
   ready structures (normalization, domains, statistics, layout, scales).
   These are memoized in the view-model hooks so they run once per dataset, not
   per render.
3. **Render to SVG.** Thin components project the view model through pure
   geometry helpers and emit SVG. Pan / zoom / filter / selection are
   client-side state; they re-render the SVG but never refetch data (except the
   Genome Browser, whose per-track loaders are region-scoped).

## Where the cost actually is

Reading the implementation identified these hot spots before any change was
made:

| Area | Hot spot | Why it is expensive at large scale |
|------|----------|------------------------------------|
| Network Viewer | Every `EdgeElement`/`NodeElement` recomputed screen geometry and re-rendered on *any* `result` change | A selection or filter change re-created the `result` object, so every node/edge re-ran projection math and re-rendered |
| Volcano / Expression | One SVG `<g>` + 2–3 circles per point; `isVolcanoHighlighted`, scale projection, and highlight counting re-run per point per render | Thousands of points → thousands of DOM nodes and O(n) per render |
| Heatmap | One `<rect>` (plus a string cell key) per matrix cell | A 1000×1000 matrix is a million DOM nodes |
| Coverage | One hit-target `<rect>` per bin plus a full path rebuild and a chromosome `.filter` per render | A dense chromosome is tens of thousands of bins |
| Distribution | Per-group statistics re-scanned the whole dataset (O(groups × values)); one `<circle>` per value | Many groups × many values, or huge groups, explode circles |
| Genome Browser | Track loaders are already region-scoped | Already correct; see below |

## Strategies

### 1. Bound the DOM with deterministic downsampling

`lib/scientific/downsample.ts` provides pure, deterministic helpers. Each is a
**no-op (pass-through) below its cap**, so small and typical datasets render at
full resolution and behavior is unchanged; only oversized datasets are reduced.

- `decimateItems(items, maxCount)` — evenly-spaced stride sample, always
  keeping the first and last elements, never exceeding `maxCount`. Used by the
  volcano plot (`MAX_RENDERED_POINTS = 2000`), the expression chart
  (`MAX_SERIES_POINTS = 1000`), and the distribution scatter
  (`MAX_SCATTER_POINTS_PER_GROUP = 1000`).
- `coverageColumns(bins, toX, plotWidth, maxColumns)` — **peak-preserving**
  (max coverage) pixel-column aggregation for coverage bins
  (`MAX_COVERAGE_COLUMNS = 2000`). Max-based binning is the standard for
  read-depth tracks (IGV-style) because averaging would hide genuine peaks.
- `aggregateHeatmap(dataset, maxRows, maxCols)` — block-average of an oversized
  expression matrix (`MAX_HEATMAP_ROWS/COLS = 150`). Each rendered cell is the
  mean of its block, so it still represents a real measurement; all-missing
  blocks stay missing.

Crucially, the **full dataset remains the source of truth** for tooltips,
selection, summaries, and detail panels. Only the marks *drawn* are decimated;
the underlying interaction reads the full data, so hover/selection never
silently reports a decimated point's neighbors.

### 2. Preserve scientific meaning

Downsampling never discards signal silently:

- Coverage aggregation keeps the **max** (peak) per pixel column.
- Distribution scatter keeps **all outliers** and stride-samples the rest.
- Heatmap aggregation reports block means (with missing preserved), and the
  chart adds a "(block-summarized for display)" note in the summary line when
  aggregation is active.
- Volcano decimation spans the whole sorted feature list evenly, so the
  effect-size distribution shape survives.

### 3. Avoid redoing work on every render

- **Memoized derived data.** Chromosome-filtered bins, aggregated coverage
  columns, rendered point/series sets, and per-group scatter samples are
  `useMemo`-derived so pan/zoom/hover re-renders reuse them.
- **Single-pass grouping.** `valuesByGroup` in `lib/scientific/distribution.ts`
  groups all distribution values in one pass; `useDistributionChart` derives
  every group's statistics from that map instead of scanning the dataset once
  per group (O(values) instead of O(groups × values)).
- **`React.memo` for large mark sets.** `NetworkViewer`'s `EdgeElement` and
  `NodeElement` are memoized and receive primitive/stable props (the node/edge,
  the memoized layout, the viewport, a `selected` boolean, and a stable
  callback). A selection change no longer recomputes projection geometry or
  re-renders every node/edge — only the viewport (pan/zoom) or the filter
  (node/edge set) forces a full re-render, which is unavoidable.
- **Memoized highlight counts.** The volcano summary's "significant at current
  thresholds" count is computed once per thresholds change instead of on every
  render.

### 4. Viewport-aware data loading (Genome Browser)

The Genome Browser already fetches **only the visible region**: each track
loader receives the settled (debounced) `GenomicInterval` and returns just the
features intersecting it (`GenomeTrackLoader` in
`lib/genome/useGenomeBrowser.ts`). Rapid pan/zoom is debounced (default 300 ms)
so navigation never fires a request per animation frame. The
`featuresInViewport` / `variantsInViewport` filters in the track components are
a defensive second clipping of already-region-scoped data. This is the primary
large-data strategy for the browser; the backend search API remains the filter
authority when it becomes reachable.

### 5. Caching policy

Caching is limited to memoization of derivations and rendered marks (above).
There is deliberately **no new cache abstraction and no cross-mount cache**: the
existing `useVisualizationData` lifecycle already re-fetches only when the
dataset id changes, and adding an app-level cache would introduce stale-data
risk without a measured benefit. If a later milestone needs one, it must define
explicit invalidation and reuse the existing hooks rather than adding a second
loading path.

## Downsampling limitations

These are intentional and documented so future work can revisit them:

- **Coverage peak-preservation** shows local maxima; a *valley* within a pixel
  column that is narrower than one pixel can be hidden (the column shows the
  peak). This matches standard read-depth rendering, but a per-pixel
  min/max band is a possible future improvement.
- **Volcano/expression decimation** renders a stride sample; two features that
  land on the same mark are not distinguished (they share a pixel anyway).
  Tooltips and selection still resolve the exact underlying feature.
- **Heatmap block-averaging** changes the *granularity* of what is shown when
  the matrix exceeds the cap; the summary line indicates this. Selection of an
  aggregated block is valid within the rendered (aggregated) matrix.
- **Distribution scatter capping** keeps outliers but reduces the visual
  density of non-outlier values in oversized groups; the box/whisker summary
  (which is full-resolution) remains the statistical authority.

## Accessibility

Large datasets may reduce visual detail but must not regress accessibility:

- Decimated marks keep the same `role="button"`, `aria-label`, `aria-pressed`,
  keyboard (Enter/Space), and focus-ring behavior as full-resolution marks.
- Tooltips and detail panels read the **full** dataset, so hover/selection is
  as accurate for large datasets as for small ones.
- Summaries and `aria-label`s report the underlying counts (full dataset), with
  an explicit "(block-summarized for display)" note when heatmap aggregation is
  active.

## Testing

Performance work is tested by algorithmic behavior, never by wall-clock timing:

- `lib/scientific/downsample.test.ts` — decimation bounds (never exceeds the
  cap, first/last preserved), determinism, coverage column peak preservation,
  and heatmap block-mean correctness (including missing-value handling).
- `lib/scientific/distribution.test.ts` — `valuesByGroup` grouping matches
  `valuesForGroup` for every group.
- All existing component tests pass unchanged, confirming the refactors are
  behavior-preserving below the caps.

## Future options

If datasets outgrow the current caps, the following are candidates (each with a
measured requirement):

- **Per-pixel min/max coverage bands** for coverage valleys.
- **Canvas/WebGL fallback** for the largest mark sets — note this is a second
  rendering architecture and is intentionally deferred (see the
  [README](README.md#technology-notes) technology constraints).
- **Worker-based statistics** for very large distributions.
- **Server-side region queries** once the Phase 5 API exposes range-based
  endpoints, moving filtering out of the client entirely.