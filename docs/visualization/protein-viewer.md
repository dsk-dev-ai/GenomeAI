# Protein Viewer (Phase 6.5)

Renders a protein's amino-acid sequence and its annotation features over a
one-based-inclusive residue window, following the same interval semantics as
the [Phase 6.2 Genome Browser](genome-browser.md). This phase is the
**sequence/annotation foundation** — it does NOT render 3D molecular structures.

## Status

Implemented on branch `feat/visualization-protein-viewer`.

## Scope (delivered)

- Typed domain model (`lib/protein/types.ts`): `Protein`, `ProteinFeature`,
  `ProteinFeatureType`, `ProteinViewport`, `ProteinResidue`,
  `ProteinViewerState`
- Pure sequence helpers (`lib/protein/sequence.ts`): 1-based residue indexing,
  amino-acid validation, window slicing
- Pure viewport math (`lib/protein/viewport.ts`): opening window, clamped
  zoom/pan/navigate, typed region parsing (`42` or `42-80`)
- Pure geometry (`lib/protein/geometry.ts`): residue/feature pixel mapping,
  axis-critical residue ticks, stable row packing, lane heights
- Feature presentation (`lib/protein/features.ts`): type normalization,
  default colours/labels, display labels, accessible labels, detail rows
- Thin typed adapter (`lib/protein/api.ts`) over the existing protein
  endpoints (`GET /proteins/{id}`, `GET /proteins/`) — no backend changes
- `useProteinViewer` hook: load lifecycle (via the shared 6.1
  `useVisualizationData`), residue window state, and feature selection
- `ProteinViewer` component: residue axis, stacked feature rows clipped to the
  visible window, residue-letter lane with per-residue numbering, region
  input, and keyboard-accessible feature selection with a detail panel
- Demo integrated at `/visualization` (`ProteinDemo`)
- Tests (104 across the protein modules) and docs

## Out of scope (later milestones or explicitly excluded)

- **3D molecular structure rendering** — this phase is sequence/annotation
  only. Structure viewing is a future milestone that would introduce
  Three.js only if 3D is truly required (see
  [README](README.md) technology notes).
- D3.js / Cytoscape.js / WebAssembly / WebGPU / C++
- Backend annotation-feature support (see
  [Feature data boundary](#feature-data-boundary))
- Dense population-scale sequence statistics / conservation plots
  (deferred to 6.9 performance work)

## Coordinate conventions

Residues are **one-based and inclusive**, matching the GenomeAI protein model:
residue `1` is the N-terminal residue, and a feature spanning `start..end`
covers residues `start` through `end` inclusive (`length = end - start + 1`).
This deliberately mirrors the Genome Browser's genomic coordinate convention
so the two viewers share identical interval semantics.

A `ProteinViewport` is a window over residues `start..end` (1-based,
inclusive); `bounds.length` carries the full protein length so navigation can
clamp pan/zoom to `1..length` exactly like the Genome Browser clamps to a
contig. The pan/zoom/clamp math is **shared** with the browser via the
structural `IntervalWindow` shape (`lib/genome/viewport.ts`), so protein
navigation cannot drift from genomic navigation.

## Architecture and data flow

```text
ProteinViewer (component)                   apps/web/src/components/protein/ProteinViewer.tsx
  useProteinViewer (view model)             apps/web/src/lib/protein/useProteinViewer.ts
    useVisualizationData (lifecycle)        + reuse lib/visualization/useVisualizationData.ts (6.1)
    fetchProtein (adapter)                  + lib/protein/api.ts
      -> GET /proteins/{id}                 + reuse lib/genome/api.ts (API_BASE_URL, errors)
  scale = createResidueScale(viewport)      + reuse lib/genome/geometry.ts (createScale)
  featuresInViewport / layoutFeatureRows    + lib/protein/geometry.ts (layoutRows)
  residuesInWindow                          + lib/protein/sequence.ts
  domain model / labels                     + lib/protein/features.ts
  viewport / parseProteinRegion             + lib/protein/viewport.ts (IntervalWindow)
```

`ProteinViewer` is fully controlled by a `ProteinViewerResult` returned from
`useProteinViewer`; the component renders nothing but presentation, so the
data lifecycle (loading / success / empty / error / retry) is handled by the
shared `VisualizationContainer`.

## Viewport and navigation

- The opening window is the first `PROTEIN_DEFAULT_WINDOW` (100) residues,
  clamped to the protein length.
- Zoom keeps the window centre fixed and never drops below
  `MIN_VIEWPORT_RESIDUES` (1) or beyond `1..length`.
- Pan moves by a fraction of the current window and clamps to the protein.
- The region input parses a single position (`42`) or an inclusive range
  (`42-80`), clamps to the protein length, and reports malformed input as a
  typed error (`parseProteinRegion`).

Because the whole protein record (sequence + features) is loaded once per
protein id, pan/zoom/navigate never refetch — they only move the residue
window client-side.

## Rendering

- **Residue axis**: tick marks at readable residues with major-position labels
  (`computeResidueTicks`), so positions stay understandable at any zoom.
- **Feature rows**: annotation features are packed onto rows
  (`layoutFeatureRows`, shared greedy row packing) and clipped to the visible
  window (`featureToPixels`). A feature bar is shown only when its interval
  overlaps the window; partially visible features render their visible slice.
- **Residue lane**: per-residue letters with 10-position number markers when
  spacing allows (`>= RESIDUE_LABEL_MIN_PX` px per residue), otherwise a
  "zoom in" hint so overlapping letters are never drawn.
- **Selection**: clicking or focusing a feature bar (Enter/Space) toggles its
  selection; the selected feature is outlined, announced via `aria-pressed`,
  and described in a labelled detail panel (`featureDetailLines`).

## Feature data boundary

The backend exposes protein identity and sequence fields (`protein_id`,
`sequence`, `length`, ...) but **does not yet expose annotation features**
(domains, motifs, active sites, ...). Therefore:

- `toProtein` returns `features: []`, and `toProteinFeature` provides the
  normalization seam a future feature endpoint will use.
- The isolated development fixture in `lib/protein/protein.fixtures.ts`
  supplies representative TP53 annotations today. It lives apart from
  production adapters, flows through the **same** normalizers
  (`toProtein`, `toProteinFeature`, `prepareFeatures`) the adapters use, and
  must be replaced — not treated as a real API — as soon as the backend
  exposes features.
- `fetchProteins` accepts an injectable `featureSource` that only enriches
  when the API did not already provide features.

## Type representation

`type` is carried as opaque text and normalized only for presentation
(`normalizeFeatureType`): known literals (domain, motif, active site, ...)
get default colours/labels, and any other string (e.g. a database-specific
term) is preserved verbatim so the viewer is not hard-wired to one annotation
source. The viewer never infers a feature class from labels or sequence.

## Accessibility

- The SVG is a labelled group (`role="group"`, `aria-label` summarizing the
  protein, residue window, and feature count) so the interactive feature
  controls stay in the accessibility tree.
- Each feature bar has a keyboard-focusable selection control
  (`role="button"`, `tabIndex=0`) with an accessible name
  (`Select <label>, residues <start>-<end>, <type>`); Enter/Space toggles
  selection, `aria-pressed` announces state, and a native `<title>` tooltip
  mirrors the detail.
- The detail panel is a labelled `<section>` with a `<dl>` of typed fields.
- Navigation controls and the residue/range input have accessible names and
  the input surfaces parse errors via `role="alert"`.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| sequence | `sequence.test.ts` | length, validation, 1-based indexing, window slicing |
| viewport | `viewport.test.ts` | opening/whole windows, zoom, pan, navigate, clamping, region parsing |
| geometry | `geometry.test.ts` | scale mapping, in-viewport clipping, rows, ticks, heights |
| features | `features.test.ts` | type normalization, colours, labels, sorting/dedup, validation |
| api | `api.test.ts` | record normalization, feature/type handling, URL, error mapping |
| hook | `useProteinViewer.test.tsx` | lifecycle states, opening window, zoom/pan/navigate/reset, selection |
| component | `ProteinViewer.test.tsx` | rendering, clipping, letter/hint lanes, selection (click + keyboard), detail panel, region input, controls |

The pre-existing genome suites (including the generalized `geometry.ts`,
`viewport.ts`, and `tracks.ts` row-packing tests) continue to pass unchanged
in behaviour.

## Files

- `apps/web/src/lib/protein/types.ts`
- `apps/web/src/lib/protein/sequence.ts`
- `apps/web/src/lib/protein/viewport.ts`
- `apps/web/src/lib/protein/geometry.ts`
- `apps/web/src/lib/protein/features.ts`
- `apps/web/src/lib/protein/api.ts`
- `apps/web/src/lib/protein/protein.fixtures.ts`
- `apps/web/src/lib/protein/useProteinViewer.ts`
- `apps/web/src/components/protein/ProteinViewer.tsx`
- `apps/web/src/app/visualization/ProteinDemo.tsx`
- `apps/web/src/app/visualization/page.tsx` (renders the demo)

Generalized base utilities (backward-compatible, reused by both viewers):

- `apps/web/src/lib/genome/geometry.ts` — `intervalToPixels` moved from the
  gene transcript geometry module
- `apps/web/src/lib/genome/viewport.ts` — `panViewport`/`zoomViewport` now
  operate on the structural `IntervalWindow`
- `apps/web/src/lib/genome/tracks.ts` — generic `layoutRows` row packing

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
