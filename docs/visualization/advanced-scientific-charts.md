# Advanced Scientific Charts (Phase 6.8)

Extends the Phase 6.7 scientific chart foundation with four reusable,
interactive scientific primitives: an **expression heatmap**, a **volcano
plot**, a **genomic coverage chart**, and a **statistical distribution chart**.
Each chart follows the same layered architecture as the earlier visualization
milestones — pure, unit-tested data modules under `lib/scientific`, a thin
view-model hook composing the shared [Phase 6.1 data lifecycle](README.md), and
presentation-only components — so future biological/scientific datasets slot
in without new infrastructure.

## Status

Implemented as part of Phase 6.8. All four charts are production-ready as
**reusable primitives** (typed data models, pure transformations, tested
components). Because the GenomeAI backend does not yet expose heatmap / volcano
/ coverage / distribution endpoints, the `/visualization` demos are
**fixture-backed** until those endpoints exist (see
[API integration](#api-integration) and [Fixture data policy](#fixture-data-policy)).

## Architecture

```text
Heatmap / VolcanoPlot / CoverageChart / DistributionChart (components)
  apps/web/src/components/scientific/{Heatmap,VolcanoPlot,CoverageChart,DistributionChart}.tsx
  useHeatmap / useVolcanoPlot / useCoverageChart / useDistributionChart (view models)
    apps/web/src/lib/scientific/use{...}.ts
    useChartData (shared lifecycle)        + lib/scientific/useChartData.ts
      useVisualizationData (lifecycle)     + reuse lib/visualization/useVisualizationData.ts (6.1)
      fetch*Dataset (adapter)              + lib/scientific/advancedApi.ts
        -> GET /advanced/{heatmaps|volcano|coverage|distributions}/{id}
    normalize*Dataset (normalize)          + lib/scientific/{heatmap,volcano,coverage,distribution}.ts
    *Domains / color scale / statistics    + lib/scientific/{heatmap,volcano,coverage,distribution}.ts
    boxPlotWhiskers / summarize            + lib/scientific/statistics.ts
  ChartAxes / ChartTooltip / ChartLegend   + reuse components/scientific/*.tsx
  genome scale / ticks / viewport          + reuse lib/genome/{geometry,viewport,types}.ts
```

Every chart is fully controlled by its `*Result` interface returned from the
corresponding hook; components render nothing but presentation, and the loading
/ success / empty / error / retry lifecycle is handled by the shared
`VisualizationContainer`.

### Shared data lifecycle (`useChartData`)

`useChartData<T>` (refactored out of the Phase 6.7 `useExpressionChart`) owns
the load pattern shared by every chart hook:

- an optional custom **loader** that takes precedence;
- a dataset-id-scoped **default loader** (`fetch*Dataset`) for the future
  backend endpoints;
- a **reload whenever the requested dataset id changes** (the loader reads the
  id through a ref, but `useVisualizationData` only fetches on mount);
- the loading / empty / success / error lifecycle from
  `useVisualizationData`, with an `isEmpty` predicate per chart.

`useExpressionChart` was refactored onto this shared hook without changing its
behavior (its 9 tests pass unchanged).

## Chart types

### 1. Expression Heatmap

Renders a `HeatmapDataset` as an interactive SVG grid: rows on the y-axis,
columns on the x-axis, and a **diverging color scale** mapping each value.
Missing values render as a distinct neutral cell. Cells expose hover tooltips
and keyboard-accessible selection with a readable detail panel.

- `heatmapValueDomain` spans all finite matrix values; `heatmapColorScale`
  maps `domain.min` → low color, `center` (default `0`) → neutral, and
  `domain.max` → high color, so negative/positive deviations read as opposites.
- Cell keys are length-prefixed (`heatmapCellKey` / `parseHeatmapCellKey`) so
  arbitrary row/column ids serialize unambiguously.
- Rows and columns are normalized to canonical (code-unit) order for
  deterministic rendering.

### 2. Volcano Plot

Renders a `VolcanoDataset` as an interactive SVG scatter plot: **effect size**
on the x-axis, **significance** on the y-axis, and points colored by whether
they pass user-supplied **highlight thresholds**. Threshold lines (dashed) mark
the callout region. Points expose hover tooltips and keyboard-accessible
selection with a readable detail panel.

Input semantics (see [Volcano semantics](#volcano-semantics)):

- `effectSize` — the effect size to plot (e.g. log fold change), finite number.
- `significance` — the y-axis value (e.g. `-log10` p-value), finite number.
- `adjustedSignificance` — optional, shown in the detail panel only.
- `metadata` — optional opaque fields shown in tooltip/detail.

The chart never infers statistical significance on its own; thresholds are a
visual callout driven by the caller's `thresholds` option.

### 3. Coverage Chart

Renders a `CoverageDataset` as an interactive SVG area chart of per-bin read
depth over a **one-based inclusive genomic interval**. The x-axis reuses the
Phase 6.2 genome coordinate utilities (`createScale`, `computeTicks`,
`formatBasePosition`) and viewport navigation comes from
`lib/genome/viewport.ts`, so intervals, ticks, and zoom/pan are shared with the
Genome Browser rather than re-implemented.

- `CoverageBin` carries `chromosome`, `start`, `end`, `coverage` — the same
  coordinate conventions as `lib/genome/types.ts` (`start >= 1`, `start <= end`).
- Chromosome controls plus zoom-in / zoom-out / pan / reset controls drive the
  view-model viewport.
- Bins expose hover tooltips and keyboard-accessible selection.

### 4. Statistical Distribution Chart

Renders a `DistributionDataset` as an interactive SVG box plot: one box per
group on the x-axis, summary quartiles/whiskers on the y-axis, and individual
values overlaid with **deterministic jitter**. Outliers are highlighted and the
group tooltip carries the summary statistics.

- Statistics come from `lib/scientific/statistics.ts` (`summarize`,
  `boxPlotWhiskers`), kept separate from rendering.
- Values are grouped deterministically (code-unit group sort, stored value
  order within a group).

## Data models

Strongly typed models live in `lib/scientific/advancedTypes.ts`:

```ts
interface HeatmapDataset {
  id: string
  title: string
  rows: string[]                         // canonical row ids
  columns: string[]                      // canonical column ids
  values: (number | undefined)[][]       // matrix, aligned to rows x columns
  rowLabels?: Record<string, string>     // display labels by row id
  columnLabels?: Record<string, string>  // display labels by column id
  metadata?: ScientificMetadata
}

interface VolcanoPoint {
  identifier: string
  effectSize: number
  significance: number
  adjustedSignificance?: number
  metadata?: ScientificMetadata
}
interface VolcanoDataset { id: string; title: string; points: VolcanoPoint[]; metadata?: ScientificMetadata }

interface CoverageBin {
  chromosome: string
  start: number
  end: number
  coverage: number
  metadata?: ScientificMetadata
}
interface CoverageDataset { id: string; title: string; bins: CoverageBin[]; metadata?: ScientificMetadata }

interface DistributionValue { group: string; value: number; metadata?: ScientificMetadata }
interface DistributionDataset { id: string; title: string; values: DistributionValue[]; metadata?: ScientificMetadata }
```

## Transformation pipeline

Each chart module (`heatmap.ts`, `volcano.ts`, `coverage.ts`,
`distribution.ts`) exposes the same pure function shape as Phase 6.7:

1. **validate** — `validate*Dataset` returns a typed error list (invalid
   identifiers, non-finite values, inverted intervals, mismatched matrices).
2. **normalize** — `normalize*Dataset` drops invalid records, dedupes
   (first wins), and produces a deterministic canonical order; the result never
   shares mutable state with the input.
3. **derive** — domains (`heatmapValueDomain`, `volcanoDomains`,
   `coverageDomain`/`coverageExtent`, `distributionGroups` + statistics).
4. **present** — tooltip builders (`heatmapCellTooltip`,
   `volcanoPointTooltip`, `coverageBinTooltip`, `distributionTooltip`) map a
   record to the labelled rows shared by the hover tooltip and the detail panel.

## Rendering pipeline

- Components measure the container with `useChartSize` and derive a `PlotArea`
  from `lib/scientific/geometry.ts`; a fixed `width`/`height` prop overrides
  the measured size for responsive layouts.
- Axes: the categorical charts (heatmap, distribution) use `ChartAxes` with
  `xScale`; the volcano plot uses the Phase 6.7 `ChartAxes` extended with a
  **continuous x-axis** (`xContinuousScale`, `xTicks`, `xFormatValue`); the
  coverage chart draws its own genomic axes via the Phase 6.2 genome geometry.
- Data is normalized/derived in the hook and memoized; per-cell/point/bin
  geometry is recomputed only when the relevant inputs change, so large
  datasets do not trigger repeated expensive transformations.
- Heatmap cells and volcano points render as `role="button"` controls
  (`tabIndex=0`, Enter/Space selection, `aria-pressed`); coverage bins render
  as `role="button"` hit areas; distribution groups expose a group hit rect
  with focus ring.

## API integration

The GenomeAI backend does **not** yet expose these endpoints. Per the
[API policy in this document](#api-integration), we did not create
duplicate endpoints: `lib/scientific/advancedApi.ts` is the smallest typed
adapter that documents the future contracts and provides the normalization
seams production will use:

- `HeatmapRecord` / `VolcanoPointRecord` / `CoverageBinRecord` /
  `DistributionValueRecord` raw-record interfaces;
- `heatmapFromRecords` / `volcanoFromRecords` / `coverageFromRecords` /
  `distributionFromRecords` normalizers shared by the fixtures and the
  adapters;
- `fetchHeatmapDataset` / `fetchVolcanoDataset` / `fetchCoverageDataset` /
  `fetchDistributionDataset` attempting
  `GET /advanced/{heatmaps|volcano|coverage|distributions}/{id}` — these 404
  today, surfacing the limitation as a typed `GenomeApiError`.

No production data is fabricated; see
[Fixture data policy](#fixture-data-policy).

## Fixture data policy

`lib/scientific/advanced.fixtures.ts` provides four small, clearly isolated,
typed fixtures (`TP53_PATHWAY_HEATMAP_FIXTURE`,
`DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE`, `TP53_WINDOW_COVERAGE_FIXTURE`,
`EXPRESSION_DISTRIBUTION_FIXTURE`). They:

- flow through the **same** normalizers the production adapters use, so every
  seam is exercised exactly as production would;
- are explicitly titled **"fixture"** and documented as arbitrary, illustrative
  values — never presented as real biological data or scientific fact;
- must be replaced by real GenomeAI data as soon as the backend exposes the
  corresponding endpoints.

The `/visualization` demos (`AdvancedScientificDemo`) load the fixtures through
the real `use*` hooks with a custom loader; the loader flips to the
`fetch*Dataset` adapter once an endpoint exists.

## Volcano semantics

- `significance` is **not** assumed to be a p-value: the chart plots whatever
  finite number the caller provides. The recommended convention is `-log10`
  p-value (higher = more significant), but the module does not assert it.
- `adjustedSignificance` is optional, purely informational, and only rendered
  in the detail panel/tooltip.
- Highlight thresholds (`effectThreshold`, `significanceThreshold`) are a
  visual callout only; `isVolcanoHighlighted` never infers statistical
  significance by itself.

## Accessibility

- Every SVG is a labelled group (`role="group"`, descriptive `aria-label`) so
  the interactive controls stay in the accessibility tree (same pattern as the
  Network Viewer).
- Cells, points, bins, and group hit rects are keyboard-focusable
  `role="button"` controls with accessible names and `aria-pressed` selection
  state; Enter/Space toggles selection.
- A native `<title>` mirrors each detail; the hover tooltip and the detail
  panel share the same labelled rows.
- Detail panels are labelled `<section>` elements with `<dl>` of typed fields.
- Loading / empty / error states render through `VisualizationContainer` with
  accessible labels; summaries announce via `aria-live="polite"`.
- A visible dashed focus ring appears on keyboard focus for volcano points and
  distribution groups.

## Performance

- All chart data is loaded once per dataset id; selection and thresholds are
  client-side only, so no per-view refetch is needed.
- Domains, statistics, and geometry are `useMemo`-cached; derivation is
  O(n) over the dataset (no O(n²) matrix rescans per render).
- Cell/point/bin hit areas are flat SVG controls — no per-frame work.
- Large-data rendering is handled deterministically in the client via the
  Phase 6.10 downsampling/aggregation layer (see [Performance](performance.md));
  a second rendering architecture (virtualization, canvas/WebGL fallback)
  remains a measured future option.

## Testing

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| statistics | `statistics.test.ts` | sorted sample, quantiles, summarize, box-plot whiskers |
| heatmap | `heatmap.test.ts` | validate (matrix consistency), normalize (canonical order, dedupe, missing values), domain/color scale, tooltip + cell keys |
| volcano | `volcano.test.ts` | validate, normalize, domains (zero significance, symmetric effect size), thresholds, tooltip |
| coverage | `coverage.test.ts` | validate intervals, normalize/dedupe/order, chromosomes/domain/extent, tooltip, reuse of genome coordinate conventions |
| distribution | `distribution.test.ts` | groups, empty groups, deterministic ordering, statistics, tooltip |
| api | `advancedApi.test.ts` | record normalization, invalid records, URL/error mapping, fixture integrity |
| shared lifecycle | `useChartData.test.tsx` | custom loader, default loader, dataset-id reload (no reload on same id), empty/error/retry, no-loader error |
| hooks | `useHeatmap` / `useVolcanoPlot` / `useCoverageChart` / `useDistributionChart` `.test.tsx` | lifecycle states, derived domains/groups, selection, chromosome selection + viewport zoom/pan/reset |
| components | `Heatmap` / `VolcanoPlot` / `CoverageChart` / `DistributionChart` `.test.tsx` | rendering, loading/empty/error/retry, hover tooltip, click + keyboard selection, aria-pressed, focus ring, detail panel, zoom/pan/chromosome controls, responsive width, degenerate datasets |

The pre-existing expression/genome/protein/network suites continue to pass
unchanged (the expression chart now runs on the shared `useChartData`).

## Files

- `apps/web/src/lib/scientific/useChartData.ts`
- `apps/web/src/lib/scientific/statistics.ts`
- `apps/web/src/lib/scientific/advancedTypes.ts`
- `apps/web/src/lib/scientific/{heatmap,volcano,coverage,distribution}.ts`
- `apps/web/src/lib/scientific/advancedApi.ts`
- `apps/web/src/lib/scientific/advanced.fixtures.ts`
- `apps/web/src/lib/scientific/use{Heatmap,VolcanoPlot,CoverageChart,DistributionChart}.ts`
- `apps/web/src/components/scientific/{Heatmap,VolcanoPlot,CoverageChart,DistributionChart}.tsx`
- `apps/web/src/components/scientific/ChartAxes.tsx` (continuous x-axis extension)
- `apps/web/src/app/visualization/AdvancedScientificDemo.tsx`
- `apps/web/src/app/visualization/page.tsx` (renders the demo)

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
