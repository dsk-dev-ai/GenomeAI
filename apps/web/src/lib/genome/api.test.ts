import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  API_BASE_URL,
  GenomeApiError,
  fetchIntervalFeatures,
  fetchVariantFeatures,
  toGeneFeature,
  toTranscriptFeature,
  toVariantFeature,
} from './api'

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

describe('toGeneFeature', () => {
  it('normalizes a raw gene record', () => {
    const feature = toGeneFeature({
      id: 'gene-1',
      gene_id: 'ENSG00000141510',
      gene_name: 'TP53',
      biotype: 'protein_coding',
      chromosome: 'chr17',
      start_position: 7_668_402,
      end_position: 7_690_000,
      strand: '-',
    })
    expect(feature.type).toBe('gene')
    expect(feature.chromosome).toBe('chr17')
    expect(feature.start).toBe(7_668_402)
    expect(feature.end).toBe(7_690_000)
    expect(feature.name).toBe('TP53')
    expect(feature.metadata).toEqual({
      geneId: 'ENSG00000141510',
      biotype: 'protein_coding',
    })
  })

  it('returns an empty feature when coordinates are missing', () => {
    const feature = toGeneFeature({ id: 'gene-2', gene_name: 'TP53', chromosome: 'chr17' })
    expect(feature.start).toBe(0)
    expect(feature.type).toBe('gene')
  })
})

describe('toTranscriptFeature', () => {
  it('normalizes a raw transcript record', () => {
    const feature = toTranscriptFeature({
      id: 'tx-1',
      transcript_id: 'ENST00000455265',
      transcript_name: 'p53 gamma-201',
      chromosome: 'chr17',
      start_position: 7_668_402,
      end_position: 7_696_976,
      strand: '-',
    })
    expect(feature.type).toBe('transcript')
    expect(feature.name).toBe('p53 gamma-201')
    expect(feature.metadata?.transcriptId).toBe('ENST00000455265')
  })

  it('returns an empty with reversed coordinates', () => {
    const feature = toTranscriptFeature({
      id: 'tx-2',
      chromosome: 'chr17',
      start_position: 900,
      end_position: 100,
    })
    expect(feature.start).toBe(0)
  })
})

describe('toVariantFeature', () => {
  it('normalizes a single-position variant record', () => {
    const feature = toVariantFeature({
      id: 'var-1',
      variant_id: 'rs113488022',
      chromosome: 'chr7',
      position: 140_453_136,
      ref: 'C',
      alt: 'T',
    })
    expect(feature.type).toBe('variant')
    expect(feature.position).toBe(140_453_136)
    expect(feature.start).toBe(140_453_136)
    expect(feature.end).toBe(140_453_136)
    expect(feature.ref).toBe('C')
    expect(feature.alt).toBe('T')
    expect(feature.name).toBe('C>T')
    expect(feature.variantId).toBe('rs113488022')
  })

  it('carries optional variant attributes when present', () => {
    const feature = toVariantFeature({
      id: 'var-3',
      variant_id: 'rs1',
      chromosome: 'chr7',
      position: 100,
      ref: 'A',
      alt: 'G',
      type: 'snv',
      quality: 99.5,
      filter_status: 'PASS',
      gene_id: 'gene-1',
      description: 'missense',
    })
    expect(feature.variantType).toBe('snv')
    expect(feature.quality).toBe(99.5)
    expect(feature.filterStatus).toBe('PASS')
    expect(feature.geneId).toBe('gene-1')
    expect(feature.description).toBe('missense')
  })

  it('leaves optional variant attributes undefined when absent', () => {
    const feature = toVariantFeature({
      id: 'var-4',
      chromosome: 'chr7',
      position: 50,
      ref: 'C',
      alt: 'T',
    })
    expect(feature.variantType).toBeUndefined()
    expect(feature.quality).toBeUndefined()
    expect(feature.filterStatus).toBeUndefined()
    expect(feature.geneId).toBeUndefined()
    expect(feature.description).toBeUndefined()
  })

  it('returns position 0 when invalid', () => {
    const feature = toVariantFeature({ id: 'var-2', chromosome: 'chr7', position: -5 })
    expect(feature.position).toBe(0)
  })
})

describe('fetchIntervalFeatures', () => {
  it('POSTs the region to the coordinate endpoint and normalizes items', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          {
            id: 'gene-1',
            gene_name: 'TP53',
            chromosome: 'chr17',
            start_position: 7_668_402,
            end_position: 7_690_020,
            strand: '-',
          },
        ],
        pagination: { page: 1, page_size: 100, total_count: 1 },
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const features = await fetchIntervalFeatures(
      'gene',
      { chromosome: 'chr17', start: 7_660_000, end: 7_700_000 },
      signal,
    )

    expect(features).toHaveLength(1)
    expect(features[0].name).toBe('TP53')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain(`${API_BASE_URL}/search/gene/coordinate`)
    const body = JSON.parse(String(init.body))
    expect(body.interval).toEqual({ chromosome: 'chr17', start: 7_660_000, end: 7_700_000 })
    expect(body.match_type).toBe('overlap')
    expect(init.signal).toBe(signal)
  })

  it('throws a GenomeApiError on non-2xx responses', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 503 } as unknown as Response)

    await expect(
      fetchIntervalFeatures('gene', { chromosome: 'chr1', start: 1, end: 100 }),
    ).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('filters out items that do not carry usable coordinates', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          { id: 'bad', chromosome: 'chr1' },
          { id: 'good', chromosome: 'chr1', start_position: 10, end_position: 20 },
        ],
        pagination: { page: 1, page_size: 100, total_count: 2 },
      }),
    )

    const features = await fetchIntervalFeatures('gene', {
      chromosome: 'chr1',
      start: 1,
      end: 100,
    })
    expect(features).toHaveLength(1)
    expect(features[0].id).toBe('good')
  })

  it('paginates until total_count is reached', async () => {
    const firstPage = Array.from({ length: 100 }, (_, i) => ({
      id: `gene-${i}`,
      gene_name: `Gene ${i}`,
      chromosome: 'chr1',
      start_position: i * 10 + 1,
      end_position: i * 10 + 10,
    }))
    const secondPage = [
      {
        id: 'gene-tail',
        gene_name: 'Tail',
        chromosome: 'chr1',
        start_position: 1,
        end_position: 10,
      },
    ]
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          items: firstPage,
          pagination: { page: 1, page_size: 100, total_count: 101 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          items: secondPage,
          pagination: { page: 2, page_size: 100, total_count: 101 },
        }),
      )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const features = await fetchIntervalFeatures('gene', {
      chromosome: 'chr1',
      start: 1,
      end: 100_000,
    })

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(features).toHaveLength(101)
    const secondCall = JSON.parse(String(fetchMock.mock.calls[1][1].body)) as {
      pagination: { page: number }
    }
    expect(secondCall.pagination.page).toBe(2)
  })

  it('throws a GenomeApiError when the payload is not an object', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(null))

    await expect(
      fetchIntervalFeatures('gene', { chromosome: 'chr1', start: 1, end: 100 }),
    ).rejects.toBeInstanceOf(GenomeApiError)
  })
})

describe('fetchVariantFeatures', () => {
  it('POSTs to the variant domain and normalizes point features', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        items: [
          { id: 'var-1', variant_id: 'rs7', chromosome: 'chr7', position: 100, ref: 'C', alt: 'T' },
        ],
        pagination: { page: 1, page_size: 100, total_count: 1 },
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const features = await fetchVariantFeatures({ chromosome: 'chr7', start: 1, end: 200 })

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/search/variant/coordinate')
    expect(JSON.parse(String(init.body)).match_type).toBe('overlap')
    expect(features).toHaveLength(1)
    expect(features[0].position).toBe(100)
  })
})
