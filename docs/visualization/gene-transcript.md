# Gene / Transcript Visualization (Phase 6.3)

Renders a gene as a lane plus one lane per transcript isoform, with intron
connectors, exon blocks, strand indicators, and labels. It reuses the [Phase
6.1 foundation](README.md) and the [Phase 6.2 Genome Browser](genome-browser.md)
coordinate and scale conventions, so it stays aligned with the browser axis.

## Status

Implemented on branch `feat/visualization-gene-transcript`.

## Scope (delivered)

- Typed domain model (`lib/genome/geneTranscript.ts`): `Gene`,
  `GeneTranscript`, `GeneExon`, validators, normalizers (`toGene`,
  `toTranscript`, `toExon`), deterministic transcript sorting, and gene
  grouping
- Pure layout geometry (`lib/genome/geneTranscriptGeometry.ts`): exon /
  transcript / gene pixel spans with viewport clipping, lane layout, total
  height, shared constants
- Thin typed data adapter (`lib/genome/geneTranscriptApi.ts`) over the Phase 5
  coordinate-search API, with an injectable exon source
- `GeneTranscriptViewer` component: gene lane with strand arrow, transcript
  lanes with intron connectors and exon blocks, hover `<title>` tips, and
  keyboard-accessible transcript selection
- Demo integrated at `/visualization` (`GeneTranscriptDemo`, TP53 fixture)
- Tests and docs

## Out of scope (later milestones or explicitly excluded)

- D3.js / Three.js / Cytoscape.js / WebAssembly / WebGPU / C++ (see
  [README](README.md) technology notes)
- Variant-call density rendering (6.4), protein / network / chart views
  (6.5–6.7)
- Exon structure from the real API (backend does not expose it yet — see
  [Exon data boundary](#exon-data-boundary))

## Architecture and data flow

```text
GeneTranscriptViewer (component)            apps/web/src/components/genome/
  scale = createScale(viewport, SVG_WIDTH)  + reuse lib/genome/geometry.ts
  lane layout / spans                       + lib/genome/geneTranscriptGeometry.ts
  domain model                              + lib/genome/geneTranscript.ts
  fetchGeneTranscripts                      + lib/genome/geneTranscriptApi.ts
    -> POST /search/{domain}/coordinate     + reuse lib/genome/api.ts (Phase 5)
      (gene | transcript) in parallel
  exon enrichment (optional ExonSource)     + lib/genome/geneTranscript.fixtures.ts (dev)
```

The viewport is the same one-based-inclusive `GenomeViewport` used by the
browser. `fetchGeneTranscripts` issues one gene and one transcript
coordinate-search (both via the shared paginating pipeline in
`lib/genome/api.ts`) in parallel, normalizes the raw items, then assigns each
transcript to its gene. No HTTP logic is duplicated and no backend changes
were made.

### Transcript-to-gene grouping

`groupTranscriptsByGene` links a transcript to a gene when either:

1. the transcript explicitly references the gene id (matching the gene's
   search-record id or its accession), or
2. the transcript has no explicit gene link (fallback) and is on the same
   chromosome with its span contained within the gene span.

Transcripts that carry a gene link to a different gene are never assigned by
coordinate containment; unlinked transcripts are dropped rather than
mis-assigned. Genes and transcripts without usable spans are filtered out by
`isValidGene` / `isValidTranscript`. Display order is deterministic
(`sortTranscripts`: start, then end, then name, then id).

## API contract used

```text
POST /search/gene/coordinate
POST /search/transcript/coordinate
```

Request body (one-based-inclusive, same shape as the browser):

```json
{
  "interval": { "chromosome": "chr17", "start": 7650000, "end": 7700000 },
  "match_type": "overlap",
  "pagination": { "page": 1, "page_size": 100 }
}
```

Gene and transcript records are normalized into the typed model
(`gene_name` → `symbol`, `start_position`/`end_position` → 1-based inclusive
`start`/`end`, `strand` `+`/`-` defaulting to `+`, optional `gene_id`,
`biotype`, `transcript_id`, `transcript_type`).

## Exon data boundary

The Phase 5 backend exposes gene and transcript spans but **not** exon
structure. This milestone therefore:

- Models `exons` on each transcript as a real, typed part of the domain.
- Returns `exons: []` from the production adapter by default.
- Provides an `ExonSource` seam (`fetchGeneTranscripts` option) so a real
  exon source can be supplied without changing the visualization.
- Ships a **development fixture** (`lib/genome/geneTranscript.fixtures.ts`)
  with TP53 and BRCA1-like data that mimics a future exon endpoint. The
  fixture is isolated: it is imported only by demos and tests, never by
  library code, and must be replaced (not treated as a real API) once the
  backend exposes exons.

## Accessibility

- The SVG is a labelled image (`role="img"`, `aria-label` describing the gene
  symbol, span, strand, and transcript count).
- Each transcript row is a keyboard-focusable control (`role="button"`,
  `tabIndex=0`) with an accessible name (`Select <name>`); Enter or Space
  toggles selection, and the selected row is announced via `aria-pressed`
  and visually highlighted.
- Hover reveals native `<title>` tooltips on the gene, transcripts, and exon
  blocks.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| model | `geneTranscript.test.ts` | normalization, strand default, validators, sorting, grouping |
| geometry | `geneTranscriptGeometry.test.ts` | spans, clipping, lanes, height |
| api | `geneTranscriptApi.test.ts` | grouping, exon source, pagination |
| component | `GeneTranscriptViewer.test.tsx` | labels, exons, selection (click + keyboard), viewport clipping |

## Files

- `apps/web/src/lib/genome/geneTranscript.ts`
- `apps/web/src/lib/genome/geneTranscriptGeometry.ts`
- `apps/web/src/lib/genome/geneTranscriptApi.ts`
- `apps/web/src/lib/genome/geneTranscript.fixtures.ts` (dev fixture)
- `apps/web/src/components/genome/GeneTranscriptViewer.tsx`
- `apps/web/src/app/visualization/GeneTranscriptDemo.tsx`
- `apps/web/src/app/visualization/page.tsx` (added the demo)
- `apps/web/src/lib/genome/api.ts` (exported `RawSearchItem` and
  `requestCoordinateSearch` for reuse)

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
