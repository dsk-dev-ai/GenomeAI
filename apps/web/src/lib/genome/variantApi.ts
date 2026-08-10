/**
 * Variant data adapter (Phase 6.4).
 *
 * Thin typed adapter over the existing Phase 5 coordinate-search API. It
 * reuses the shared request pipeline in `lib/genome/api.ts`
 * (`POST /search/variant/coordinate` with one-based-inclusive intervals) —
 * no duplicate HTTP logic and no backend changes.
 *
 * The backend treats variants as single-position records: the variant domain
 * maps both `start` and `end` columns to the `position` column, so an
 * "overlap" query returns every variant whose single position falls inside
 * the requested interval.
 */

import { requestCoordinateSearch } from './api'
import type { RawSearchItem } from './api'
import type { GenomicInterval } from './types'
import { isValidVariant, toVariant } from './variant'
import type { Variant } from './variant'

export interface FetchVariantsOptions {
  /** Page size forwarded to the coordinate-search API. */
  pageSize?: number
}

function asRawItems(items: unknown[]): RawSearchItem[] {
  return items.filter(
    (value): value is RawSearchItem =>
      typeof value === 'object' && value !== null && !Array.isArray(value),
  )
}

/**
 * Fetches variants whose single position overlaps `interval` and returns
 * them as typed `Variant` records. Reuses the shared coordinate-search
 * pipeline and the caller's `AbortSignal`.
 */
export async function fetchVariants(
  interval: GenomicInterval,
  signal?: AbortSignal,
  options: FetchVariantsOptions = {},
): Promise<Variant[]> {
  const items = await requestCoordinateSearch('variant', interval, signal, options.pageSize ?? 100)
  return asRawItems(items).map(toVariant).filter(isValidVariant)
}
