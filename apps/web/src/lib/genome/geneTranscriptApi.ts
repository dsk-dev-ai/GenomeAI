/**
 * Gene / Transcript data adapter (Phase 6.3).
 *
 * Thin typed adapter over the existing Phase 5 coordinate-search API. It
 * reuses the shared request pipeline in `lib/genome/api.ts`
 * (`POST /search/{domain}/coordinate` with one-based-inclusive intervals) —
 * no duplicate HTTP logic and no backend changes.
 *
 * ## Exon boundary
 *
 * The Phase 5 API does **not** expose exon structure. The adapter therefore
 * returns transcripts with `exons: []`, and an optional `exonSource` can
 * enrich them. Enrichment only runs when the API did not already provide
 * exons, so a future backend exon source is never overwritten. Production
 * callers that need exon blocks should supply a real source once the backend
 * exposes one; the isolated development fixture in
 * `lib/genome/geneTranscript.fixtures.ts` is the current substitute and must
 * be replaced, not treated as a real API.
 */

import { requestCoordinateSearch } from './api'
import type { RawSearchItem } from './api'
import { groupTranscriptsByGene, toGene, toTranscript } from './geneTranscript'
import type { Gene, GeneExon, GeneTranscript } from './geneTranscript'
import type { GenomicInterval } from './types'

/** Supplies exon blocks for a transcript (future real-API seam). */
export type ExonSource = (transcript: GeneTranscript) => GeneExon[]

const EMPTY_EXONS: ExonSource = () => []

function asRawItems(items: unknown[]): RawSearchItem[] {
  return items.filter(
    (value): value is RawSearchItem =>
      typeof value === 'object' && value !== null && !Array.isArray(value),
  )
}

export interface FetchGeneTranscriptsOptions {
  /** Page size forwarded to the coordinate-search API. */
  pageSize?: number
  /** Enriches each transcript with exon blocks (see module docs). */
  exonSource?: ExonSource
}

/**
 * Fetches genes and transcripts overlapping `interval` and groups transcripts
 * under their gene. Both domain requests go through the shared
 * coordinate-search pipeline and share the caller's `AbortSignal`.
 */
export async function fetchGeneTranscripts(
  interval: GenomicInterval,
  signal?: AbortSignal,
  options: FetchGeneTranscriptsOptions = {},
): Promise<Gene[]> {
  const pageSize = options.pageSize ?? 100
  const exonSource = options.exonSource ?? EMPTY_EXONS

  const [geneItems, transcriptItems] = await Promise.all([
    requestCoordinateSearch('gene', interval, signal, pageSize),
    requestCoordinateSearch('transcript', interval, signal, pageSize),
  ])

  const genes = asRawItems(geneItems).map(toGene)
  const transcripts = asRawItems(transcriptItems).map(toTranscript)

  return groupTranscriptsByGene(genes, transcripts).map((gene) => ({
    ...gene,
    transcripts: gene.transcripts.map((transcript) => ({
      ...transcript,
      exons: transcript.exons.length > 0 ? transcript.exons : exonSource(transcript),
    })),
  }))
}
