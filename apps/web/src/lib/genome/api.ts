/**
 * GenomeAI API data adapter for the Genome Browser (Phase 6.2).
 *
 * Reuses the Phase 5 coordinate-search endpoint:
 *
 *     POST /search/{domain}/coordinate
 *
 * with a one-based inclusive `interval` and `match_type: "overlap"`. The
 * browser only ever requests the currently visible region, never whole
 * chromosomes. Domain column mapping and match semantics stay on the
 * backend; this module serializes the request and normalizes the (untyped)
 * `items` array into typed `GenomicFeature` / `VariantFeature` records.
 *
 * These loaders accept an `AbortSignal` and therefore satisfy the
 * Phase 6.1 `VisualizationLoader` contract. React never touches storage.
 */

import type { GenomicFeature, GenomicInterval, VariantFeature } from './types'

/** Base URL of the GenomeAI API. */
export const API_BASE_URL = process.env.NEXT_PUBLIC_GENOMEAI_API_URL ?? 'http://localhost:8000'

/** Domains that support coordinate search (Phase 5). */
export type CoordinateDomain = 'gene' | 'variant' | 'transcript'

/** Error thrown for non-2xx API responses. */
export class GenomeApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message)
    this.name = 'GenomeApiError'
  }
}

interface PaginationPayload {
  page: number
  page_size: number
  total_count: number
}

interface CoordinateSearchPayload {
  items: unknown[]
  pagination?: PaginationPayload
}

type RawSearchItem = Record<string, unknown>

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

function asNumber(value: unknown): number | undefined {
  return typeof value === 'number' ? value : undefined
}

function idOf(value: unknown): string {
  if (typeof value === 'string' && value.length > 0) return value
  if (typeof value === 'object' && value !== null && 'id' in value) {
    return idOf((value as { id: unknown }).id)
  }
  return ''
}

function strandOf(value: unknown): GenomicFeature['strand'] {
  return value === '+' || value === '-' ? value : undefined
}

function withOptional<T>(key: string, value: T | undefined): Record<string, T> {
  return value === undefined ? {} : { [key]: value }
}

/** Normalizes a raw gene record from the search API. */
export function toGeneFeature(item: RawSearchItem): GenomicFeature {
  const start = asNumber(item.start_position)
  const end = asNumber(item.end_position)
  const chromosome = asString(item.chromosome)
  const valid = chromosome !== undefined && start !== undefined && end !== undefined && start <= end
  if (!valid) return { ...EMPTY_FEATURE, type: 'gene' }

  return {
    id: idOf(item.id),
    type: 'gene',
    chromosome,
    start,
    end,
    strand: strandOf(item.strand),
    name: asString(item.gene_name),
    metadata: {
      ...withOptional('geneId', asString(item.gene_id)),
      ...withOptional('biotype', asString(item.biotype)),
    },
  }
}

const EMPTY_FEATURE: GenomicFeature = {
  id: '',
  type: 'unknown',
  chromosome: '',
  start: 0,
  end: 0,
}

/** Normalizes a raw transcript record from the search API. */
export function toTranscriptFeature(item: RawSearchItem): GenomicFeature {
  const start = asNumber(item.start_position)
  const end = asNumber(item.end_position)
  const chromosome = asString(item.chromosome)
  const valid = chromosome !== undefined && start !== undefined && end !== undefined && start <= end
  if (!valid) return { ...EMPTY_FEATURE, type: 'transcript' }

  return {
    id: idOf(item.id),
    type: 'transcript',
    chromosome,
    start,
    end,
    strand: strandOf(item.strand),
    name: asString(item.transcript_name),
    metadata: {
      ...withOptional('transcriptId', asString(item.transcript_id)),
      ...withOptional('transcriptType', asString(item.transcript_type)),
    },
  }
}

/** Normalizes a raw variant record (single-position model). */
export function toVariantFeature(item: RawSearchItem): VariantFeature {
  const position = asNumber(item.position)
  const chromosome = asString(item.chromosome)
  if (chromosome === undefined || position === undefined || position < 1) {
    return { ...EMPTY_FEATURE, type: 'variant', position: 0 }
  }
  const ref = asString(item.ref)
  const alt = asString(item.alt)
  return {
    id: idOf(item.id),
    type: 'variant',
    chromosome,
    start: position,
    end: position,
    position,
    ref,
    alt,
    name: ref && alt ? `${ref}>${alt}` : undefined,
    metadata: { ...withOptional('variantId', asString(item.variant_id)) },
  }
}

export interface CoordinateSearchOptions {
  pageSize?: number
}

/** Hard cap applied by the Phase 5 coordinate-search backends. */
const MAX_COORDINATE_RESULTS = 10_000

/**
 * Fetches every page of a coordinate search for the visible interval, up to
 * `pagination.total_count`. The API caps result sets (Phase 5), so a dense
 * region cannot silently truncate at the first page.
 */
async function requestCoordinateSearch(
  domain: CoordinateDomain,
  interval: GenomicInterval,
  signal: AbortSignal | undefined,
  pageSize: number,
): Promise<unknown[]> {
  const collected: unknown[] = []
  let page = 1

  for (;;) {
    if (signal?.aborted) throw new DOMException('The operation was aborted.', 'AbortError')

    const response = await fetch(`${API_BASE_URL}/search/${domain}/coordinate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interval: { chromosome: interval.chromosome, start: interval.start, end: interval.end },
        match_type: 'overlap',
        pagination: { page, page_size: pageSize },
      }),
      signal,
    })

    if (!response.ok) {
      throw new GenomeApiError(
        `GenomeAI API returned ${response.status} for ${domain} region ${interval.chromosome}:${interval.start}-${interval.end}`,
        response.status,
      )
    }

    const payload = (await response.json()) as CoordinateSearchPayload | null
    if (payload === null || typeof payload !== 'object') {
      throw new GenomeApiError(
        `GenomeAI API returned an invalid payload for ${domain} region ${interval.chromosome}:${interval.start}-${interval.end}`,
      )
    }

    const items = Array.isArray(payload.items) ? payload.items : []
    collected.push(...items)

    const totalCount = payload.pagination?.total_count
    const fetched = collected.length
    if (
      items.length === 0 ||
      totalCount === undefined ||
      fetched >= totalCount ||
      fetched >= MAX_COORDINATE_RESULTS
    ) {
      return collected
    }
    page += 1
  }
}

function asRawItems(items: unknown[]): RawSearchItem[] {
  return items.filter(
    (value): value is RawSearchItem =>
      typeof value === 'object' && value !== null && !Array.isArray(value),
  )
}

/** Fetches interval features (genes or transcripts) for a visible region. */
export async function fetchIntervalFeatures(
  domain: Exclude<CoordinateDomain, 'variant'>,
  interval: GenomicInterval,
  signal?: AbortSignal,
  options: CoordinateSearchOptions = {},
): Promise<GenomicFeature[]> {
  const items = await requestCoordinateSearch(domain, interval, signal, options.pageSize ?? 100)
  const normalize = domain === 'gene' ? toGeneFeature : toTranscriptFeature
  return asRawItems(items)
    .map(normalize)
    .filter((feature) => feature.start > 0 && feature.end >= feature.start)
}

/** Fetches point variants for a visible region. */
export async function fetchVariantFeatures(
  interval: GenomicInterval,
  signal?: AbortSignal,
  options: CoordinateSearchOptions = {},
): Promise<VariantFeature[]> {
  const items = await requestCoordinateSearch('variant', interval, signal, options.pageSize ?? 100)
  return asRawItems(items)
    .map(toVariantFeature)
    .filter((feature) => feature.position >= 1)
}
