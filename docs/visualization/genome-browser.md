# Genome Browser (Phase 6.2)

An interactive, accessible viewport over a chromosome that renders tracked
genomic features (genes and, as single-position marks, variants). It is the
first concrete visualization built on the [Phase 6.1 foundation](README.md).

## Status

Implemented on branch `feat/visualization-genome-browser`.

## Scope (delivered)

- One-based inclusive coordinate model (`lib/genome/types.ts`)
- Chromosome normalization / validation mirroring the backend pattern
- Region parsing (`chr1:100000-200000`) with typed error codes
- Pure viewport math: zoom (factor, clamped), pan (clamped), whole-contig
  and initial viewports
- Pixel geometry: scale, nice ticks, base-position axis labelling
- Track architecture: greedy non-overlapping row layout and viewport
  clipping
- `useGenomeBrowser` hook: debounced per-track region fetch via the 6.1
  `useVisualizationData` lifecycle (loading / success / empty / error)
- `GenomeBrowser` component: axis, per-track lanes, navigation controls and
  a region input, all reusing `VisualizationContainer`
- Thin typed data adapter over the Phase 5 coordinate-search API
- Demo integrated at `/visualization`

## Out of scope (later milestones or explicitly excluded)

- D3.js / Three.js / Cytoscape.js / WebAssembly / WebGPU / C++ (see
  [README](README.md) technology notes)
- Full variant-call density rendering (6.4), transcript structure (6.3)
- Chromosome-ideogram virtualized mega-contigs (6.9 performance work)

## Architecture and data flow

```
GenomeBrowser (component)                    apps/web/src/components/genome/
  useGenomeBrowser -> useState(viewport)  +  apps/web/src/lib/genome/useGenomeBrowser.ts
      useVisualizationData (per track)    + reuse of lib/visualization/useVisualizationData.ts
        fetchIntervalFeatures / fetchVariantFeatures
         -> POST /search/{domain}/coordinate        (Phase 5)
```

The viewport is the single source of truth for navigation. Every user action
(zoom, pan button, reset, region input) produces a new immutable viewport via
`lib/genome/viewport.ts`. Track loaders receive the *visible interval only*,
so requests stay bounded regardless of contig size, and rapid pan/zoom is
debounced (300 ms) before a region change triggers new fetches.

## API contract used

The browser reuses the existing Phase 5 search endpoint — no backend changes
were made in this milestone:

```text
POST /search/{domain}/coordinate        (domain = gene | variant | transcript)
```

Request body (relevant fields) and one-based-inclusive semantics:

```json
{
  "interval": { "chromosome": "chr17", "start": 7_650_000, "end": 7_700_000 },
  "match_type": "overlap",
  "pagination": { "page": 1, "page_size": 100 }
}
```

`lib/genome/api.ts` serializes the request (including the `overlap` match so
a base exactly on a feature edge is included) and normalizes the untyped
`items` array into `GenomicFeature` / `VariantFeature`. Non-2xx responses are
surfaced as `GenomeApiError`.

## Accessibility

- Per-track lanes are rendered inside `VisualizationContainer` (each has a
  heading and its own loading / empty / error semantics).
- Viewport navigation is a labelled `fieldset` group of buttons with
  `aria-label`s.
- The region form has an explicit `<label>` for its input.
- The current region and span are an `<output>` with `aria-live="polite"`.
- Decorating SVG text is `aria-hidden`; interactive feature metadata lives
  in `<title>` tips only for success content, keeping the SVG itself
  non-interactive.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| chromosome | `chromosome.test.ts` | normalize / validate |
| region | `region.test.ts` | parse + error codes |
| viewport | `viewport.test.ts` | zoom / pan clamping |
| geometry | `geometry.test.ts` | scale, ticks, labels |
| tracks | `tracks.test.ts` | row layout, in-viewport filter |
| api | `api.test.ts` | request shape + normalization |
| hook | `useGenomeBrowser.test.tsx` | per-track status + debounced refetch |
| component | `GenomeBrowser.test.tsx` | controls, region navigation, states |

## Files

- `apps/web/src/lib/genome/types.ts`
- `apps/web/src/lib/genome/chromosome.ts`
- `apps/web/src/lib/genome/region.ts`
- `apps/web/src/lib/genome/viewport.ts`
- `apps/web/src/lib/genome/geometry.ts`
- `apps/web/src/lib/genome/tracks.ts`
- `apps/web/src/lib/genome/api.ts`
- `apps/web/src/lib/genome/useGenomeBrowser.ts`
- `apps/web/src/components/genome/GenomeBrowser.tsx`
- `apps/web/src/app/visualization/GenomeBrowserDemo.tsx`

## Validation

All commands green on the branch:

```
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```