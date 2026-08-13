import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE_URL } from './api'
import { fetchVariants } from './variantApi'

const rawFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = rawFetch
  vi.restoreAllMocks()
})

function jsonResponse(payload: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(payload),
  } as Response
}

describe('fetchVariants', () => {
  it('POSTs to the variant coordinate endpoint and normalizes point features', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          {
            id: 'var-1',
            variant_id: 'rs113488022',
            chromosome: 'chr7',
            position: 140_453_136,
            ref: 'C',
            alt: 'T',
            type: 'snv',
            quality: 99.5,
            filter_status: 'PASS',
          },
        ],
        pagination: { page: 1, page_size: 100, total_count: 1 },
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const variants = await fetchVariants(
      { chromosome: 'chr7', start: 140_000_000, end: 141_000_000 },
      signal,
    )

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain(`${API_BASE_URL}/search/variant/coordinate`)
    const body = JSON.parse(String(init.body)) as {
      interval: { chromosome: string; start: number; end: number }
      match_type: string
    }
    expect(body.interval).toEqual({ chromosome: 'chr7', start: 140_000_000, end: 141_000_000 })
    expect(body.match_type).toBe('overlap')
    expect(init.signal).toBe(signal)

    expect(variants).toHaveLength(1)
    expect(variants[0]).toMatchObject({
      id: 'var-1',
      variantId: 'rs113488022',
      chromosome: 'chr7',
      position: 140_453_136,
      variantType: 'snv',
      quality: 99.5,
      filterStatus: 'PASS',
    })
  })

  it('filters out items without usable coordinates', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          { id: 'bad', chromosome: 'chr7', position: -1 },
          { id: 'good', chromosome: 'chr7', position: 10, ref: 'C', alt: 'T' },
        ],
        pagination: { page: 1, page_size: 100, total_count: 2 },
      }),
    )

    const variants = await fetchVariants({ chromosome: 'chr7', start: 1, end: 100 })
    expect(variants).toHaveLength(1)
    expect(variants[0].id).toBe('good')
  })

  it('filters out records with neither id nor variant_id so selection stays stable', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          { chromosome: 'chr7', position: 10 },
          { id: 'named', variant_id: 'rs1', chromosome: 'chr7', position: 20 },
        ],
        pagination: { page: 1, page_size: 100, total_count: 2 },
      }),
    )

    const variants = await fetchVariants({ chromosome: 'chr7', start: 1, end: 100 })
    expect(variants).toHaveLength(1)
    expect(variants[0].id).toBe('named')
  })
})
