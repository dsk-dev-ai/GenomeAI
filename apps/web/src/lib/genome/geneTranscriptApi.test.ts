import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE_URL } from './api'
import { fetchGeneTranscripts } from './geneTranscriptApi'

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

const interval = { chromosome: 'chr17', start: 7_660_000, end: 7_700_000 }

describe('fetchGeneTranscripts', () => {
  it('requests genes and transcripts for the interval and groups them', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'gene-tp53',
              gene_id: 'ENSG00000141510',
              gene_name: 'TP53',
              biotype: 'protein_coding',
              chromosome: 'chr17',
              strand: '+',
              start_position: 7_665_901,
              end_position: 7_690_000,
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'tx-1',
              transcript_id: 'ENST00000269305',
              transcript_name: 'TP53-201',
              chromosome: 'chr17',
              strand: '+',
              start_position: 7_665_901,
              end_position: 7_690_000,
              gene_id: 'gene-tp53',
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const genes = await fetchGeneTranscripts(interval, signal)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    const [firstUrl, firstInit] = fetchMock.mock.calls[0] as [string, RequestInit]
    const [secondUrl, secondInit] = fetchMock.mock.calls[1] as [string, RequestInit]

    expect(firstUrl).toBe(`${API_BASE_URL}/search/gene/coordinate`)
    expect(secondUrl).toBe(`${API_BASE_URL}/search/transcript/coordinate`)
    expect(firstInit.signal).toBe(signal)
    expect(secondInit.signal).toBe(signal)

    const firstBody = JSON.parse(String(firstInit.body))
    expect(firstBody.interval).toEqual(interval)
    expect(firstBody.match_type).toBe('overlap')

    expect(genes).toHaveLength(1)
    expect(genes[0].symbol).toBe('TP53')
    expect(genes[0].transcripts).toHaveLength(1)
    expect(genes[0].transcripts[0].name).toBe('TP53-201')
    // API does not expose exons, so they are empty by default.
    expect(genes[0].transcripts[0].exons).toEqual([])
  })

  it('applies an exonSource to enrich transcripts', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'gene-tp53',
              gene_name: 'TP53',
              chromosome: 'chr17',
              start_position: 100,
              end_position: 1000,
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'tx-1',
              transcript_name: 'TP53-201',
              chromosome: 'chr17',
              start_position: 200,
              end_position: 800,
              gene_id: 'gene-tp53',
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const genes = await fetchGeneTranscripts(interval, undefined, {
      exonSource: () => [{ start: 300, end: 400 }],
    })

    expect(genes[0].transcripts[0].exons).toEqual([{ start: 300, end: 400 }])
  })

  it('drops unlinked transcripts rather than mis-assigning them', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'gene-tp53',
              gene_name: 'TP53',
              chromosome: 'chr17',
              start_position: 100,
              end_position: 1000,
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          items: [
            {
              id: 'tx-other',
              transcript_name: 'FAR-AWAY',
              chromosome: 'chr2',
              start_position: 500,
              end_position: 600,
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        }),
      )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const genes = await fetchGeneTranscripts(interval)
    expect(genes[0].transcripts).toEqual([])
  })

  it('paginates both domains through the shared request pipeline', async () => {
    let genePage = 0
    const fetchMock = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/gene/')) {
        genePage += 1
        return jsonResponse({
          items: [
            {
              id: `g${genePage}`,
              gene_name: `Gene ${genePage}`,
              chromosome: 'chr17',
              start_position: 7_660_000 + genePage,
              end_position: 7_660_100 + genePage,
            },
          ],
          pagination: { page: genePage, page_size: 1, total_count: 2 },
        })
      }
      if (url.includes('/transcript/')) {
        return jsonResponse({
          items: [
            {
              id: 'tx-1',
              transcript_name: 'TP53-201',
              chromosome: 'chr17',
              start_position: 7_660_050,
              end_position: 7_660_200,
              gene_id: 'g1',
            },
          ],
          pagination: { page: 1, page_size: 100, total_count: 1 },
        })
      }
      return jsonResponse({ items: [], pagination: { page: 1, page_size: 100, total_count: 0 } })
    })
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const genes = await fetchGeneTranscripts(interval)

    // Gene domain: page 1 returns total_count 2 > page_size 1 → second page
    // follows the same loop; the shared pipeline requests both pages.
    const geneCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/gene/'))
    expect(geneCalls.length).toBeGreaterThanOrEqual(2)
    expect(genes).toHaveLength(2)
    expect(genes.find((g) => g.id === 'g1')?.transcripts).toHaveLength(1)
  })
})
