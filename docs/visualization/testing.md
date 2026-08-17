# Visualization Testing

Phase 6.11 — Visualization Testing & Documentation. This document maps test
coverage across the Phase 6 platform, records the conventions the suite
follows, and explains how to run it. The milestone audited every Phase 6
module, added behavior/correctness/edge tests where coverage was thin, fixed a
latent bug the audit uncovered, and added focused component + accessibility
tests for previously untested pieces.

## Coverage map

The full web suite is **813 tests across 68 files** (deterministic, no
timing-based benchmarks). Coverage by module:

| Module | Files | Focus |
|--------|-------|-------|
| Visualization foundation | `components/visualization/VisualizationContainer.test.tsx` (10), `lib/visualization/useVisualizationData.test.tsx` (13), `lib/visualization/visualizationModules.test.ts` (6) | loading/empty/error/content states, retry, a11y semantics, stale-response handling, abort on unmount, refetch lifecycle, module-catalog data contract, fresh-copy semantics, delay/failure/abort |
| Genome Browser + genes + variants | `components/genome/*` (30), `lib/genome/*` (178) | coordinate model + region parsing (valid/malformed/boundaries), viewport pan/zoom clamping (incl. window-wider-than-contig), track stacking + tie-breaking, Genome Browser navigation/zoom/track lifecycle, debounce collapse, in-flight aborts, data-contract edge cases (string positions, gene strand, pagination, 10,000 cap, abort between pages) |
| Protein Viewer | `components/protein/ProteinViewer.test.tsx` (16), `lib/protein/*` (89) | sequence/viewport/geometry, feature selection, detail panel, a11y |
| Network Viewer | `components/network/NetworkViewer.test.tsx` (14), `lib/network/*` (84) | layout determinism, filtering, viewport, node/edge selection, a11y |
| Scientific charts + advanced charts | `components/scientific/*` (85), `lib/scientific/*` (258) | scales/geometry, validation + normalization, statistics (quantiles, whiskers, single-element), deterministic downsampling/aggregation (exact caps, ragged blocks, NaN/Infinity), per-chart transforms (heatmap/volcano/coverage/distribution), chart hooks (domains, selection, selection-clearing), chart primitives (axes/labels/legend/tooltip clamping), API adapters (URLs, normalization, error mapping, abort) |
| Research Workspace | `components/workspace/*` (19), `lib/workspace/*` (11) | research-context state, context-select a11y, data-source contract, panel rendering, loading/error/retry states, whole-dataset panels independent of context changes, region-driven remounting |

Phase 6.11 added coverage in bolded areas: `visualizationModules.test.ts` (new),
`useChartSize.test.tsx` (new), `ChartPrimitives.test.tsx` (new), plus expanded
`downsample`, `region`, `viewport`, `tracks`, `useGenomeBrowser`, `api`,
`advancedApi`, `statistics`, `useVolcanoPlot`, `useVisualizationData`, and
`ResearchWorkspace` suites.

## What the audit caught

- **`panViewport` clamp bug**: a window wider than the contig panned right could
  produce a `start` below base 1. Fixed in `lib/genome/viewport.ts` by clamping
  `start = Math.max(1, end - span + 1)` (matching `zoomViewport`), with
  regression + edge tests.
- **Untested modules**: `visualizationModules.ts` and `useChartSize.ts` had no
  tests — both now covered.
- **Untested components**: `ChartAxes`, `ChartLegend`, `ChartTooltip` had no
  direct tests (the container test covered only the shared states) — now
  covered, including the tooltip on-screen clamp and legend list semantics.
- **Thin lifecycle coverage**: the shared data hooks lacked tests for
  selection-clearing on reload, stale errors, data clearing during refetch,
  and abort timing — all added.

## Conventions

- **Behavior over implementation**: assertions target rendered output, roles,
  accessible names, and observable state — never internal call sequences.
- **Deterministic**: fake timers for debounce/delay tests; `FakeResizeObserver`
  for sizing tests. No wall-clock assertions.
- **Flush pattern**: after `waitFor(...)` confirms a state change, settle React
  updates with `await act(async () => {})` before making follow-up selection or
  navigation changes, to avoid act-environment flakes (mirrors the
  `useNetworkViewer` / `useProteinViewer` / `useHeatmap` pattern).
- **Promise handling**: attach `expect(promise).rejects…` **before** triggering
  the rejection (e.g. calling `controller.abort()`), so the rejection is never
  reported as unhandled by Vitest.
- **No fakes that assert internals**: mocks supply data or signals, never
  replace the behavior under test.

## Running

- Web suite: `pnpm --filter @genomeai/web test` (Vitest + Testing Library).
- Single file: `pnpm --filter @genomeai/web exec vitest run <path>` from
  `apps/web`.
- Full project: `make test` (web + backend pytest).

## Intentional gaps

- **No timing-based performance benchmarks**: Phase 6.10 coverage is
  deterministic (downsampling output is asserted, not timed).
- **Per-pixel / visual-regression tests** are out of scope for now; SVG
  geometry is asserted through the pure `lib/*/geometry` modules instead.
- Future visualization milestones should keep the per-module testing
  convention documented here (pure modules unit-tested, components exercised
  through Testing Library with role/name queries, a11y semantics asserted).