import { afterEach, describe, expect, it, vi } from 'vitest'

import { GenomeApiError } from '@/lib/genome/api'

import {
  fetchProtein,
  fetchProteins,
  isValidProtein,
  proteinUrl,
  toProtein,
  toProteinFeature,
} from './api'
import type { Protein } from './types'

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

describe('toProtein', () => {
  it('normalizes a raw protein record', () => {
    const protein = toProtein({
      id: 'a1b2c3',
      protein_id: 'P04637',
      protein_name: 'Cellular tumor antigen p53',
      symbol: 'P53',
      accession: 'P04637',
      sequence: 'MEEPQSDPSV',
      length: 10,
      organism: 'Homo sapiens',
      function: 'tumor suppressor',
      description: 'Tumor suppressor p53',
    })
    expect(protein.id).toBe('a1b2c3')
    expect(protein.proteinId).toBe('P04637')
    expect(protein.name).toBe('P53')
    expect(protein.sequence).toBe('MEEPQSDPSV')
    expect(protein.length).toBe(10)
    expect(protein.organism).toBe('Homo sapiens')
    expect(protein.description).toBe('Tumor suppressor p53')
  })

  it('falls back to protein_id for the id and derives length from the sequence', () => {
    const protein = toProtein({ protein_id: 'P04637', protein_name: 'P53', sequence: 'MEEPQSDPSV' })
    expect(protein.id).toBe('P04637')
    expect(protein.name).toBe('P53')
    expect(protein.length).toBe(10)
    expect(protein.proteinId).toBe('P04637')
  })

  it('falls back to the function text when no description is present', () => {
    const protein = toProtein({
      id: 'p1',
      protein_name: 'P53',
      sequence: 'M',
      function: 'repairs DNA',
    })
    expect(protein.description).toBe('repairs DNA')
  })

  it('returns features [] because the backend does not expose them yet', () => {
    const protein = toProtein({ id: 'p1', protein_name: 'P53', sequence: 'M' })
    expect(protein.features).toEqual([])
  })

  it('handles an empty sequence record', () => {
    const protein = toProtein({ id: 'p1', protein_name: 'P53' })
    expect(protein.sequence).toBe('')
    expect(protein.length).toBe(0)
  })
})

describe('toProteinFeature', () => {
  it('normalizes a raw feature record', () => {
    const feature = toProteinFeature({
      id: 'f1',
      start: 94,
      end: 292,
      type: 'domain',
      label: 'p53 DNA-binding',
      description: 'sequence-specific DNA binding',
      accession: 'IPR012346',
      metadata: { evidence: 'inferred' },
    })
    expect(feature.id).toBe('f1')
    expect(feature.start).toBe(94)
    expect(feature.end).toBe(292)
    expect(feature.type).toBe('domain')
    expect(feature.label).toBe('p53 DNA-binding')
    expect(feature.description).toBe('sequence-specific DNA binding')
    expect(feature.accession).toBe('IPR012346')
    expect(feature.metadata?.evidence).toBe('inferred')
  })

  it('preserves unknown types verbatim and defaults missing spans to 0', () => {
    const feature = toProteinFeature({ id: 'f2', type: 'my-custom-tag', name: 'Tag' })
    expect(feature.type).toBe('my-custom-tag')
    expect(feature.label).toBe('Tag')
    expect(feature.start).toBe(0)
    expect(feature.end).toBe(0)
  })
})

describe('isValidProtein', () => {
  it('accepts a complete protein', () => {
    const protein: Protein = { id: 'p1', name: 'P53', sequence: 'MEEPQ', length: 5, features: [] }
    expect(isValidProtein(protein)).toBe(true)
  })

  it('rejects empty or invalid sequences', () => {
    expect(isValidProtein({ id: 'p1', name: 'P53', sequence: '', length: 0, features: [] })).toBe(
      false,
    )
    expect(
      isValidProtein({ id: 'p1', name: 'P53', sequence: 'M-X', length: 3, features: [] }),
    ).toBe(false)
  })
})

describe('fetchProtein', () => {
  it('GETs the protein endpoint and normalizes the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: 'a1b2c3',
        protein_id: 'P04637',
        protein_name: 'p53',
        sequence: 'MEEPQSDPSV',
        length: 10,
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const protein = await fetchProtein('P04637', signal)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe(proteinUrl('P04637'))
    expect(init.signal).toBe(signal)
    expect(protein.id).toBe('a1b2c3')
    expect(protein.length).toBe(10)
  })

  it('throws a GenomeApiError on a non-2xx response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 } as unknown as Response)
    await expect(fetchProtein('P04637')).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('throws a GenomeApiError on a malformed payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(null))
    await expect(fetchProtein('P04637')).rejects.toBeInstanceOf(GenomeApiError)
  })
})

describe('fetchProteins', () => {
  it('normalizes the catalog and drops invalid records', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse([
        { id: 'p1', protein_id: 'P04637', protein_name: 'p53', sequence: 'MEEPQSDPSV', length: 10 },
        { id: 'p2', protein_name: 'broken' },
      ]),
    )
    const proteins = await fetchProteins()
    expect(proteins).toHaveLength(1)
    expect(proteins[0].id).toBe('p1')
  })

  it('enriches features from a featureSource when the API provides none', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse([{ id: 'p1', protein_name: 'p53', sequence: 'MEEPQ', length: 5 }]),
      )
    const proteins = await fetchProteins({
      featureSource: () => [{ id: 'f1', start: 1, end: 3, type: 'domain', label: 'D' }],
    })
    expect(proteins[0].features).toHaveLength(1)
    expect(proteins[0].features[0].id).toBe('f1')
  })

  it('throws a GenomeApiError on a malformed catalog', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse({ items: [] }))
    await expect(fetchProteins()).rejects.toBeInstanceOf(GenomeApiError)
  })
})
