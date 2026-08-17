# Visualization Architecture

## Overview

The visualization platform follows the layered architecture shown below. The key
invariant is that **visualization components never touch storage** — they consume
data through the visualization data layer, which resolves it via the GenomeAI
API/SDK.

```text
Next.js / React (UI)
      │
      ▼
Visualization Components          e.g. GenomeBrowser, ExpressionChart, NetworkViewer,
      │                                 ProteinViewer, ResearchWorkspace, chart primitives
      ▼
Visualization Foundation
      ├── Types            (apps/web/src/lib/visualization/types.ts)
      ├── Container        (apps/web/src/components/visualization/VisualizationContainer.tsx)
      ├── States           (VisualizationLoading / VisualizationEmpty / VisualizationErrorState)
      ├── Data Adapter     (apps/web/src/lib/visualization/useVisualizationData.ts)
      └── Catalog          (apps/web/src/lib/visualization/visualizationModules.ts)
      │
      ▼
GenomeAI API / SDK
      │
      ▼
FastAPI → PostgreSQL
```

## Component Structure

The foundation and all Phase 6 modules live in the web application:

```text
apps/web/src/
├── components/
│   ├── visualization/            VisualizationContainer + loading/empty/error states
│   ├── genome/                   GenomeBrowser, VariantTrack, GeneTranscriptViewer
│   ├── protein/                  ProteinViewer
│   ├── network/                  NetworkViewer
│   ├── scientific/               ExpressionChart, Heatmap, VolcanoPlot,
│   │                             CoverageChart, DistributionChart, ChartAxes,
│   │                             ChartLegend, ChartTooltip
│   └── workspace/                ResearchWorkspace + panels + fixture data source
├── lib/
│   ├── visualization/            types, useVisualizationData, module catalog
│   ├── genome/                   types, region/viewport/geometry/tracks,
│   │                             useGenomeBrowser, API adapters
│   ├── protein/                  types, sequence/viewport/geometry, useProteinViewer, API
│   ├── network/                  types, model/normalize/filter/layout/viewport, API
│   ├── scientific/               chart types/scales/geometry, statistics, downsample,
│   │                             heatmap/volcano/coverage/distribution, hooks, API adapters
│   └── workspace/                researchContext, dataSources
└── app/visualization/
    ├── page.tsx                  Route (/visualization) — demo catalog
    ├── VisualizationDemo.tsx     Client demo proving the architecture
    └── workspace/page.tsx        Research Workspace route (/visualization/workspace)
```

## Data Flow

1. A visualization component calls `useVisualizationData(loader)` with a typed
   loader that returns `Promise<T>`.
2. The hook owns the request lifecycle and exposes `status`, `data`, `error`,
   and `refetch`.
3. The component passes `status`/`error` to `VisualizationContainer`, which
   renders exactly one state: loading, empty, error, or content.
4. Loaders resolve data through the GenomeAI API/SDK (or, during 6.1, a
   placeholder). Visualization components never import database code.

### Request cancellation

`useVisualizationData` passes an `AbortSignal` to every loader. When a newer
request supersedes an in-flight one, or the component unmounts, the signal is
aborted and stale responses are discarded. Loaders must throw an
`AbortError`-named error on abort (for example by passing the signal to
`fetch`); the hook ignores these by design.

## How Future Modules Should Integrate

1. Add a typed loader for the domain data (e.g. `fetchGenomeTracks`) that
   resolves through the GenomeAI API/SDK and accepts `(signal: AbortSignal)`.
2. Create the visualization component using `useVisualizationData`.
3. Render it inside `VisualizationContainer`, which already provides the
   heading, description, and loading / empty / error states.
4. Add a route under `apps/web/src/app/` and register the module in
   `visualizationModules.ts` for the demo catalog.
5. Add tests following `useVisualizationData.test.tsx` /
   `VisualizationContainer.test.tsx`.

## Loading / Empty / Error Conventions

| State    | Rendered by                     | Notes |
|----------|--------------------------------|-------|
| Loading  | `VisualizationLoading`          | `role="status"`, politely announced |
| Empty    | `VisualizationEmpty`            | human-readable message, e.g. "No samples match the selection." |
| Error    | `VisualizationErrorState`       | `role="alert"`, message, optional keyboard-accessible Retry |
| Success  | the container's children        | domain content is rendered by the consumer |

## Accessibility

- The container is a `<section aria-labelledby>` whose `<h2>` title names it.
- Page routes use a single `<h1>`; containers contribute `<h2>` headings.
- Loading is announced via `role="status"`; error via `role="alert"`.
- The retry control is a native `<button>` (keyboard accessible).
- State is never conveyed by color alone: loading, empty, and error states all
  include text labels.

## Responsive Design

- Containers fill their parent width with responsive padding (`p-4 sm:p-6`).
- Content areas scroll horizontally when necessary (`overflow-auto`).
- The demo page uses a `grid-cols-1 lg:grid-cols-2` layout; the module list
  inside it uses `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.

Performance optimization for very large data sets is delivered in Phase 6.10
(deterministic downsampling/aggregation and per-render work reduction); see
[Performance](./performance.md).

## Tests

| File | Covers |
|------|--------|
| `components/visualization/VisualizationContainer.test.tsx` | normal/loading/empty/error/content rendering, accessibility semantics, retry |
| `lib/visualization/useVisualizationData.test.tsx` | success, error, empty, loading, stale-response handling, abort on unmount, refetch, refetch lifecycle |
| `lib/visualization/visualizationModules.test.ts` | module-catalog data contract (ids, titles, milestones), fresh-copy semantics, delay/failure/abort |

Coverage for the 6.2–6.10 modules is documented per module (see the linked
docs in [README.md](./README.md#documents)); the Phase 6.11 testing pass maps
and extends that coverage (see [Testing](./testing.md)).

Run with `pnpm --filter @genomeai/web test`.