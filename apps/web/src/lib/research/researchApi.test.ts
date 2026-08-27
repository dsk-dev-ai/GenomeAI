import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE_URL } from './client'
import { analyzeGeneDiseases, searchDiseases } from './diseaseApi'
import { searchDrugs } from './drugApi'
import { analyzeGene } from './geneApi'
import { searchLiterature } from './literatureApi'
import { analyzePathway } from './pathwayApi'
import { analyzeProtein } from './proteinApi'
import { generateReport } from './reportApi'
import { interpretVariant } from './variantApi'

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

function mockFetch(payload: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(jsonResponse(payload))
  globalThis.fetch = fetchMock as unknown as typeof fetch
  return fetchMock
}

describe('research API client', () => {
  it('analyzeGene POSTs to /api/v1/genes/analyze with symbol', async () => {
    const fetchMock = mockFetch({ gene_symbol: 'BRCA1' })
    const result = await analyzeGene('BRCA1')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE_URL}/api/v1/genes/analyze`)
    expect(JSON.parse(init.body as string)).toEqual({
      symbol: 'BRCA1',
      organism: 'Homo sapiens',
    })
    expect(result.gene_symbol).toBe('BRCA1')
  })

  it('interpretVariant POSTs to /api/v1/variants/interpret with hgvs_c', async () => {
    const fetchMock = mockFetch({ gene_symbol: 'BRCA1' })
    await interpretVariant('BRCA1', 'c.5074G>A')

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toEqual({
      gene: 'BRCA1',
      hgvs_c: 'c.5074G>A',
      clinvar_id: '',
    })
  })

  it('analyzeProtein POSTs to /api/v1/proteins/analyze', async () => {
    const fetchMock = mockFetch({ accession: 'P38398' })
    await analyzeProtein('BRCA1')

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE_URL}/api/v1/proteins/analyze`)
  })

  it('searchLiterature POSTs to /api/v1/literature/search with max_results', async () => {
    const fetchMock = mockFetch({ europepmc_count: 5 })
    await searchLiterature('BRCA1', 5)

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toEqual({ query: 'BRCA1', max_results: 5 })
  })

  it('searchDrugs POSTs to /api/v1/drugs/search', async () => {
    const fetchMock = mockFetch({ chembl_drugs: [] })
    await searchDrugs('BRCA1')

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE_URL}/api/v1/drugs/search`)
  })

  it('analyzePathway POSTs to /api/v1/pathways/analyze', async () => {
    const fetchMock = mockFetch({ reactome_pathways: [] })
    await analyzePathway('BRCA1')

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(JSON.parse(init.body as string)).toEqual({ gene: 'BRCA1', genes: [] })
  })

  it('searchDiseases and analyzeGeneDiseases POST correctly', async () => {
    const searchMock = mockFetch({ diseases: [] })
    await searchDiseases('breast cancer')
    expect(JSON.parse((searchMock.mock.calls[0][1] as RequestInit).body as string)).toEqual({
      query: 'breast cancer',
    })

    const geneMock = mockFetch({ diseases: [] })
    await analyzeGeneDiseases('BRCA1')
    expect(geneMock.mock.calls[0][0] as string).toContain('/api/v1/diseases/gene')
  })

  it('generateReport POSTs to /api/v1/reports/multi-domain', async () => {
    const fetchMock = mockFetch({ gene: 'BRCA1', sources: [] })
    await generateReport('BRCA1')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(`${API_BASE_URL}/api/v1/reports/multi-domain`)
    expect(JSON.parse(init.body as string)).toEqual({ gene: 'BRCA1', variant: '' })
  })

  it('throws a readable error when the response is not ok', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      json: () => Promise.resolve({ detail: 'boom' }),
    } as Response)
    globalThis.fetch = fetchMock as unknown as typeof fetch

    await expect(analyzeGene('BRCA1')).rejects.toThrow('boom')
  })
})
