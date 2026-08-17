# Scientific Charts (Phase 6.7)

Provides the first scientific chart — an **expression chart** (samples on the
x-axis, expression values on the y-axis, one series per gene) — on top of a
small, reusable chart foundation: typed measurement datasets, native scales
and tick generation, axes, legends, tooltips, and keyboard-accessible point
selection. It follows the same layered architecture as the earlier
visualization milestones — pure, unit-tested math under `lib/scientific`, a
thin view-model hook, and presentation-only components over the shared
[Phase 6.1 foundation](README.md).

## Status

Implemented as part of Phase 6.7.

## Design decision: native scales, no D3.js

The Phase 6.1 technology notes anticipated D3.js for Phase 6.7. This
milestone deliberately delivers the chart **foundation without that
dependency**: linear value scales, category (sample) scales, and human-friendly
tick generation are implemented natively in TypeScript and rendered with plain
SVG, consistent with the platform's lightweight stance.

Consequences and rationale:

- **Determinism first.** "Same input, stable output" is a hard requirement for
  scientific visualization and for tests. `createContinuousScale`,
  `createCategoryScale`, and `niceTicks` are pure, allocation-free of shared
  state, and locale independent — charts render identically across runs and
  environments.
- **Zero new dependencies.** The web app remains React + TypeScript + Tailwind
  + SVG. This matches how the genome/protein viewers re-implemented their own
  scale/axis math (`lib/genome/geometry.ts`).
- **A clean seam.** Scales are plain interfaces (`ContinuousScale`,
  `CategoryScale`); a D3-backed or logarithmic scale could be added later
  without touching the component or the hook.
- If heavy statistical charting (many marks, animated transitions, a large
  grammar-of-graphics API) becomes a real requirement, the scale seam is where
  D3.js would plug in.

## Scope (delivered)

- Typed data model (`lib/scientific/types.ts`): `ExpressionPoint`,
  `ExpressionSeries`, `ExpressionDataset`, `PointKey` — deliberately generic
  about measurement *kind*, so later scientific charts (coverage, statistical
  comparisons, QC metrics, ...) reuse the same dataset and infrastructure.
- Pure validation + normalization (`lib/scientific/expression.ts`):
  `validateExpressionDataset` (typed error list), `normalizeExpressionDataset`
  (drop invalid points, dedupe by entity + sample, deterministic ordering),
  `availableSamples`, `seriesDomain` / `datasetDomain`, `expressionValueDomain`
  (zero-anchored / padded defaults), `hasRenderablePoints`,
  `hasNormalizedValues`, `sanitizeMetadata`.
- Native scales (`lib/scientific/scale.ts`): `createContinuousScale`
  (value → pixel, invertible), `createCategoryScale` (even sample slots),
  `niceTicks` / `continuousNiceTickStep` (1/2/5 × 10^n steps, negative +
  fractional domains), `formatTickValue`, `categoryLabelTicks` (deterministic
  label stepping when samples do not fit).
- Pure chart geometry (`lib/scientific/geometry.ts`): chart/plot dimensions,
  margins, `plotArea`, and the deterministic colorblind-aware `SERIES_COLORS`
  palette.
- Tooltip mapping (`lib/scientific/tooltip.ts`): `pointTooltip` builds the
  labelled rows (sample, value, normalized value, metadata) shared by the hover
  tooltip and the accessible detail panel; `lookupPoint` resolves a `PointKey`.
- Thin typed adapter (`lib/scientific/api.ts`): documented expected contract
  for a future expression endpoint plus normalization seams —
  **no backend changes** (see [API limitation](#api-limitation)).
- `useExpressionChart` hook: load lifecycle (via the shared 6.1
  `useVisualizationData`), sorted samples, active value field (raw /
  normalized toggle with safe fallback), y-domain, and point selection.
- Responsive sizing (`useChartSize`): measures the container via
  `ResizeObserver` with a deterministic fallback.
- Reusable chart primitives (`components/scientific/`): `ChartAxes`
  (gridlines + tick labels + captions), `ChartLegend`, `ChartTooltip`, and the
  `ExpressionChart` component composing them.
- Demo integrated at `/visualization` (`ScientificDemo`).
- Tests and docs.

## Out of scope (later milestones or explicitly excluded)

- Other chart types (coverage, volcano, heatmap, statistical comparison, QC).
  The dataset model and scale/geometry/tooltip infrastructure were designed to
  be reused by them.
- Logarithmic / transformed scales and error bars.
- D3.js / WebAssembly / WebGPU (see design decision above).
- Backend expression endpoints (see [API limitation](#api-limitation)).
- Large-data rendering work beyond the Phase 6.10 downsampling caps (measured
  future option; see the roadmap).
- Import from external biological databases (GEO, ArrayExpress, TCGA, ...).
  The browser never talks to them; they feed GenomeAI through the later
  connector/ingestion architecture.

## Data model

```ts
interface ExpressionPoint {
  identifier: string       // measured entity, e.g. gene symbol
  sample: string           // categorical x-axis group
  value: number            // measurement shown on the y-axis
  normalizedValue?: number // alternative representation (z-score, log ratio, ...)
  metadata?: ScientificMetadata
}

interface ExpressionSeries {
  id: string
  label: string
  points: ExpressionPoint[]
}

interface ExpressionDataset {
  id: string
  title: string
  series: ExpressionSeries[]
  metadata?: ScientificMetadata
}
```

A point is uniquely identified by the triple `(seriesId, identifier, sample)` —
one series contains one measurement per entity per sample, so the identity is
serialized as `seriesId:identifier@sample` (`pointKeyToString` /
`parsePointKey`) and used for selection, keyboard navigation, and tooltips.

## Architecture and data flow

```text
ExpressionChart (component)                 apps/web/src/components/scientific/ExpressionChart.tsx
  useExpressionChart (view model)           apps/web/src/lib/scientific/useExpressionChart.ts
    useVisualizationData (lifecycle)        + reuse lib/visualization/useVisualizationData.ts (6.1)
    fetchExpressionDataset (adapter)        + lib/scientific/api.ts
      -> GET /expression/datasets/{id}      + reuse lib/genome/api.ts (API_BASE_URL, errors)
    normalizeExpressionDataset (normalize)  + lib/scientific/expression.ts
    availableSamples / valueDomain          + lib/scientific/expression.ts
  createContinuousScale / CategoryScale     + lib/scientific/scale.ts
  plotArea / seriesColor                    + lib/scientific/geometry.ts
  pointTooltip / lookupPoint                + lib/scientific/tooltip.ts
  ChartAxes / ChartLegend / ChartTooltip    + components/scientific/*.tsx
```

`ExpressionChart` is fully controlled by an `ExpressionChartResult` returned
from `useExpressionChart`; the component renders nothing but presentation, so
the data lifecycle (loading / success / empty / error / retry) is handled by
the shared `VisualizationContainer`.

## Rendering

- The y-axis is a `ContinuousScale` over `expressionValueDomain`; all-
  non-negative measurements start at zero, all-negative measurements end at
  zero, and degenerate single-value datasets are padded.
- The x-axis is a `CategoryScale` over the sorted, unique sample names;
  sample labels are stepped deterministically when they do not fit.
- Each series (gene) gets a stable palette color and a connecting polyline
  through its (sample, value) positions; points that lack the active value
  field (e.g. no normalized value in normalized view) are skipped.
- A "Value / Normalized" control toggles the y-axis between `value` and
  `normalizedValue`; it only appears when the dataset carries normalized
  values.
- Hovering a point shows a `ChartTooltip`; selecting a point (click or
  Enter/Space) shows the labelled detail panel and highlights the point.

## API limitation

The GenomeAI backend does **not** yet expose an expression endpoint. Therefore:

- `lib/scientific/api.ts` documents the expected contract
  (`RawExpressionDatasetRecord` / `RawExpressionSeriesRecord` /
  `RawExpressionPointRecord`), provides the normalization seams
  (`toExpressionPoint`, `toExpressionSeries`, `expressionDatasetFromRecords`),
  and `fetchExpressionDataset` attempts `GET /expression/datasets/{id}` (which
  404s today, surfacing the limitation as a typed `GenomeApiError`).
- The isolated development fixtures in `lib/scientific/expression.fixtures.ts`
  supply representative TP53-pathway expression values today. They live apart
  from production adapters, flow through the **same** normalizers the adapters
  use, and must be replaced — not treated as a real API — as soon as the
  backend exposes an expression endpoint.

## Expression semantics

- Raw `value`s are treated as opaque finite numbers; the chart does **not**
  assert biological validity, log-transform anything, or hard-code gene /
  disease / database knowledge. Negative and zero values are supported because
  they are scientifically meaningful for normalized ratios and low/absent
  expression.
- Normalized values are purely presentational alternatives selected by the
  toggle; `expressionValueDomain` adapts the y-axis accordingly.

## Accessibility

- The SVG is a labelled group (`role="group"`, `aria-label` summarizing the
  dataset, sample count, and series count) so the interactive point controls
  stay in the accessibility tree.
- Each point is a keyboard-focusable selection control (`role="button"`,
  `tabIndex=0`) with an accessible name (e.g. `Select TP53: TP53 in Tumor-1 =
  128.4`); Enter/Space toggles selection, `aria-pressed` announces state, and a
  native `<title>` mirrors the detail.
- The detail panel is a labelled `<section>` with a `<dl>` of typed fields;
  the hover tooltip uses the same rows.
- The summary is announced via `aria-live="polite"`; the value-field toggle is
  a `<fieldset>` with accessible buttons.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| validation | `expression.test.ts` | point/series/dataset validation, duplicate series ids, zero/negative values |
| normalization | `expression.test.ts` | deterministic ordering, dedupe by entity + sample, invalid drops, default fallbacks |
| derived data | `expression.test.ts` | samples, per-series/dataset domains, zero-anchored / padded / safe domains, metadata sanitizing |
| scale | `scale.test.ts` | continuous mapping + invert, inverted ranges, negative domains, category spacing, nice ticks, label stepping |
| geometry | `geometry.test.ts` | plot area from margins, clamping, deterministic palette |
| tooltip | `tooltip.test.ts` | row mapping (with/without normalized + metadata), format, unique point lookup |
| api | `api.test.ts` | record normalization, invalid-record handling, URL, error mapping, fixture integrity |
| hook | `useExpressionChart.test.tsx` | lifecycle states, empty/error/retry, derived samples + domain, field toggle + fallback, selection reset-on-new-dataset |
| component | `ExpressionChart.test.tsx` | rendering, axes/legend, point selection (click + keyboard), hover tooltip, detail panel, value-field toggle, responsive width, degenerate datasets |

The pre-existing genome/protein/network suites continue to pass unchanged.

## Files

- `apps/web/src/lib/scientific/types.ts`
- `apps/web/src/lib/scientific/expression.ts`
- `apps/web/src/lib/scientific/scale.ts`
- `apps/web/src/lib/scientific/geometry.ts`
- `apps/web/src/lib/scientific/tooltip.ts`
- `apps/web/src/lib/scientific/api.ts`
- `apps/web/src/lib/scientific/expression.fixtures.ts`
- `apps/web/src/lib/scientific/useChartSize.ts`
- `apps/web/src/lib/scientific/useExpressionChart.ts`
- `apps/web/src/components/scientific/ChartAxes.tsx`
- `apps/web/src/components/scientific/ChartLegend.tsx`
- `apps/web/src/components/scientific/ChartTooltip.tsx`
- `apps/web/src/components/scientific/ExpressionChart.tsx`
- `apps/web/src/app/visualization/ScientificDemo.tsx`
- `apps/web/src/app/visualization/page.tsx` (renders the demo)

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
