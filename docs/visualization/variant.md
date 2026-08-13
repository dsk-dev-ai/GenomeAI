# Variant Visualization (Phase 6.4)

Renders variants as coordinate-accurate point marks in a reusable track lane,
integrated with the [Phase 6.2 Genome Browser](genome-browser.md) track
architecture and reusing its one-based-inclusive coordinate and scale
conventions. Selecting a variant reveals a readable detail panel.

## Status

Implemented on branch `feat/visualization-variant`.

> **Known limitation — live data blocked by the backend (pre-existing, not
> from this phase).** The Phase 5 coordinate-search endpoints return raw
> SQLAlchemy ORM objects in `items: list[Any]`, so any search that returns
> rows fails JSON serialization with a `PydanticSerializationError` (HTTP 500),
> and `/search/suggestions` fails on a `SELECT DISTINCT ... ORDER BY` error.
> The demo therefore calls the **real** `/search/variant/coordinate` endpoint
> (no fixtures or mocked responses) and renders the track's error state until
> the backend is fixed; the fixture-based gene/transcript viewer is unaffected.
> A backend fix is tracked as a separate issue in the repository (search
> endpoints must serialize ORM rows to `RawSearchItem` records before
> responding).

## Scope (delivered)

- Typed domain model (`lib/genome/variant.ts`): `Variant` (reuses the existing
  `VariantFeature` type), normalizer `toVariant`, `isValidVariant` validator,
  display helpers (`variantLabel`, `variantAccessibleLabel`,
  `variantDetailLines`)
- Pure point geometry (`lib/genome/variantGeometry.ts`): in-viewport filtering
  for single positions, pixel mapping via the shared scale, deterministic row
  stacking so dense or identical marks never fully overlap, lane height
- Thin typed data adapter (`lib/genome/variantApi.ts`) over the Phase 5
  coordinate-search API (`fetchVariants`) — no backend changes
- `VariantTrack` component: coordinate-accurate point marks, hover `<title>`
  tips, keyboard-accessible variant selection (`role="button"`,
  Enter/Space, `aria-pressed`), and a detail panel
- The Genome Browser now renders any `kind: 'variants'` track through the
  reusable `VariantTrack` instead of an inline branch
- Demo integrated at `/visualization` (`GenomeBrowserDemo` variants track)
- Tests and docs

## Out of scope (later milestones or explicitly excluded)

- D3.js / Three.js / Cytoscape.js / WebAssembly / WebGPU / C++ (see
  [README](README.md) technology notes)
- Dense variant-call / histogram density rendering at population scale
  (deferred to 6.9 performance work)
- Protein / network / chart views (6.5–6.7)

## Architecture and data flow

```text
GenomeBrowser (component)                    apps/web/src/components/genome/
  BrowserTrack                                dispatches by kind
    kind === 'variants' -> VariantTrack       apps/web/src/components/genome/VariantTrack.tsx
      useGenomeTrack (data lifecycle)         + reuse lib/genome/useGenomeBrowser.ts
      scale = createScale(viewport)           + reuse lib/genome/geometry.ts
      variantsInViewport / layoutVariantMarks + lib/genome/variantGeometry.ts
      domain model / labels                   + lib/genome/variant.ts
      fetchVariants                           + lib/genome/variantApi.ts
        -> POST /search/variant/coordinate    + reuse lib/genome/api.ts (Phase 5)
```

The viewport is the same one-based-inclusive `GenomeViewport` used by the
browser. `VariantTrack` follows the same track lifecycle as the built-in
lanes (`useGenomeTrack` + `useVisualizationData`), so loading, empty, error,
and retry states are handled consistently by `VisualizationContainer`.

## Point coordinate semantics

The GenomeAI variant model is a **single-position** record:

- One `position` (1-based, `>= 1`) — there is no `end_position`.
- No strand.
- A variant is "in viewport" when it is on the same chromosome and
  `viewport.start <= position <= viewport.end` (one-based inclusive), matching
  the overlap semantics of the coordinate-search API.

The frontend never fabricates `end` or strand values; `start === end ===
position` in the feature record.

## API contract used

```text
POST /search/variant/coordinate
```

Request body (one-based-inclusive, same shape as the browser):

```json
{
  "interval": { "chromosome": "chr17", "start": 7650000, "end": 7700000 },
  "match_type": "overlap",
  "pagination": { "page": 1, "page_size": 100 }
}
```

The variant domain maps both the `start` and `end` search columns to the
`position` column, so an overlap query returns every variant whose single
position falls inside the interval.

Records are normalized into the typed model: `variant_id` → `variantId`
(also used as the fallback `id`), `type` → `variantType`, `quality` (number),
`filter_status` → `filterStatus`, `gene_id` → `geneId`, `description`,
`ref`/`alt`, and `position` (1-based).

### Type representation

`type` is a free-form, nullable string on the backend (e.g. `snv`) with no
enumerated vocabulary. The frontend therefore:

- Carries `variantType` as opaque text and renders it verbatim in labels,
  tooltips, and the detail panel.
- Never infers a variant class from arbitrary strings or from `ref`/`alt`
  lengths. `ref>alt` is used only as a display label, not a classification.

Only fields the API actually reports appear in the detail panel.

## Mark layout

Marks are positioned with the shared scale (`createScale`), so they align with
the browser axis. `layoutVariantMarks` then stacks marks greedily onto rows:
variants are sorted by position (then id), and each mark is placed on the
first row whose rightmost mark lies at least `VARIANT_MIN_SEPARATION` (5 px)
to the left. Identical or adjacent positions therefore remain individually
visible. The lane height grows by `VARIANT_ROW_HEIGHT` per row so stacked
marks never clip.

## Accessibility

- The SVG is a labelled group (`role="group"`, `aria-label` summarizing the
  track label and variant count) so the interactive variant controls stay in
  the accessibility tree.
- Each variant mark is a keyboard-focusable control (`role="button"`,
  `tabIndex=0`) with an accessible name (`Select <label>, <chrom>:<pos>[,
  <type>][, filter <status>]`); Enter or Space toggles selection, and the
  selected mark is announced via `aria-pressed` and visually highlighted.
- Hover reveals a native `<title>` tooltip with the same readable detail.
- The detail panel is a labelled `<section>` with a `<dl>` of typed fields.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| model | `variant.test.ts` | normalization, id fallback, validators, labels, detail lines |
| geometry | `variantGeometry.test.ts` | in-viewport filtering, pixel mapping, row stacking, separation, height |
| api | `variantApi.test.ts` | endpoint/body/interval, optional fields, invalid-item filtering |
| component | `VariantTrack.test.tsx` | rendering, viewport clipping, stacking, selection (click + keyboard), detail panel, error/retry |

The Genome Browser suite (`GenomeBrowser.test.tsx`) continues to pass with the
variants lane now delegated to `VariantTrack`.

## Files

- `apps/web/src/lib/genome/variant.ts`
- `apps/web/src/lib/genome/variantGeometry.ts`
- `apps/web/src/lib/genome/variantApi.ts`
- `apps/web/src/components/genome/VariantTrack.tsx`
- `apps/web/src/lib/genome/types.ts` (enriched `VariantFeature` with
  `variantId`, `variantType`, `quality`, `filterStatus`, `geneId`,
  `description`)
- `apps/web/src/lib/genome/api.ts` (enriched `toVariantFeature` mapping)
- `apps/web/src/components/genome/GenomeBrowser.tsx` (delegates variants kind
  to `VariantTrack`)
- `apps/web/src/app/visualization/GenomeBrowserDemo.tsx` (uses `fetchVariants`)
- `apps/web/src/app/visualization/page.tsx` (already renders the demo)

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
