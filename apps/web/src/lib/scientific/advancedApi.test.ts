import { afterEach, describe, expect, it, vi } from 'vitest'

import { API_BASE_URL, GenomeApiError } from '@/lib/genome/api'

import { TP53_PATHWAY_HEATMAP_FIXTURE } from './advanced.fixtures'
import {
  coverageFromRecords,
  distributionFromRecords,
  fetchCoverageDataset,
  fetchDistributionDataset,
  fetchHeatmapDataset,
  fetchVolcanoDataset,
  heatmapFromRecords,
  toCoverageBin,
  toDistributionValue,
  toVolcanoPoint,
  volcanoFromRecords,
} from './advancedApi'

const rawFetch = globalThis.fetch

function jsonResponse(payload: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(payload),
  } as Response
}

afterEach(() => {
  globalThis.fetch = rawFetch
  vi.restoreAllMocks()
})

describe('heatmapFromRecords', () => {
  it('builds a normalized heatmap from raw records', () => {
    const heatmap = heatmapFromRecords({
      id: 'h1',
      title: 'H1',
      rows: ['b', 'a'],
      columns: ['y', 'x'],
      values: [
        [1, 2],
        [3, 4],
      ],
      row_labels: { a: 'A' },
    })
    expect(heatmap).toBeDefined()
    expect(heatmap?.rows).toEqual(['a', 'b'])
    expect(heatmap?.columns).toEqual(['x', 'y'])
    expect(heatmap?.rowLabels).toEqual({ a: 'A' })
  })

  it('returns undefined for a record without an id', () => {
    expect(heatmapFromRecords({ title: 'H1' })).toBeUndefined()
  })

  it('coerces non-finite values to undefined', () => {
    const heatmap = heatmapFromRecords({
      id: 'h1',
      rows: ['a'],
      columns: ['x'],
      values: [[Number.NaN]],
    })
    expect(heatmap?.values[0][0]).toBeUndefined()
  })

  it('normalizes the fixture into a renderable dataset', () => {
    expect(TP53_PATHWAY_HEATMAP_FIXTURE.rows.length).toBeGreaterThan(0)
    expect(TP53_PATHWAY_HEATMAP_FIXTURE.columns.length).toBeGreaterThan(0)
    expect(TP53_PATHWAY_HEATMAP_FIXTURE.values).toHaveLength(
      TP53_PATHWAY_HEATMAP_FIXTURE.rows.length,
    )
  })
})

describe('toVolcanoPoint / volcanoFromRecords', () => {
  it('normalizes a raw volcano point', () => {
    const point = toVolcanoPoint({ identifier: 'g1', effect_size: 1.5, significance: 4.2 })
    expect(point).toEqual({ identifier: 'g1', effectSize: 1.5, significance: 4.2 })
  })

  it('accepts camelCase effect size and adjusted significance', () => {
    const point = toVolcanoPoint({
      identifier: 'g1',
      effectSize: 1,
      significance: 2,
      adjustedSignificance: 1.5,
    })
    expect(point?.adjustedSignificance).toBe(1.5)
  })

  it('returns undefined for invalid points', () => {
    expect(toVolcanoPoint({ effect_size: 1, significance: 2 })).toBeUndefined()
    expect(toVolcanoPoint({ identifier: 'g1', significance: 2 })).toBeUndefined()
    expect(
      toVolcanoPoint({ identifier: 'g1', effect_size: Number.NaN, significance: 2 }),
    ).toBeUndefined()
  })

  it('builds a normalized volcano dataset from records', () => {
    const volcano = volcanoFromRecords({
      id: 'v1',
      title: 'V1',
      points: [
        { identifier: 'b', effect_size: 1, significance: 2 },
        { identifier: 'a', effect_size: -1, significance: 3 },
      ],
    })
    expect(volcano?.points.map((point) => point.identifier)).toEqual(['a', 'b'])
  })
})

describe('toCoverageBin / coverageFromRecords', () => {
  it('normalizes a raw coverage bin', () => {
    const bin = toCoverageBin({ chromosome: 'chr1', start: 1, end: 100, coverage: 42 })
    expect(bin).toEqual({ chromosome: 'chr1', start: 1, end: 100, coverage: 42 })
  })

  it('returns undefined for an invalid bin', () => {
    expect(toCoverageBin({ chromosome: 'chr1', start: 1, end: 100 })).toBeUndefined()
    expect(toCoverageBin({ chromosome: 'chr1', start: 1, end: 1.5, coverage: 1 })).toBeUndefined()
  })

  it('builds a normalized coverage dataset from records', () => {
    const coverage = coverageFromRecords({
      id: 'c1',
      title: 'C1',
      bins: [
        { chromosome: 'chr2', start: 1, end: 5, coverage: 1 },
        { chromosome: 'chr1', start: 1, end: 5, coverage: 2 },
      ],
    })
    expect(coverage?.bins.map((bin) => bin.chromosome)).toEqual(['chr1', 'chr2'])
  })
})

describe('toDistributionValue / distributionFromRecords', () => {
  it('normalizes a raw distribution value', () => {
    const value = toDistributionValue({ group: 'Tumor', value: 4.5 })
    expect(value).toEqual({ group: 'Tumor', value: 4.5 })
  })

  it('returns undefined for an invalid value', () => {
    expect(toDistributionValue({ group: '', value: 1 })).toBeUndefined()
    expect(toDistributionValue({ group: 'Tumor' })).toBeUndefined()
  })

  it('builds a normalized distribution dataset from records', () => {
    const distribution = distributionFromRecords({
      id: 'd1',
      title: 'D1',
      values: [
        { group: 'Tumor', value: 1 },
        { group: 'Normal', value: 2 },
      ],
    })
    expect(distribution?.values.map((value) => value.group)).toEqual(['Normal', 'Tumor'])
  })
})

describe('fetch*Dataset adapters', () => {
  it('fetches and normalizes a heatmap dataset', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: 'h-live',
        title: 'Live',
        rows: ['b', 'a'],
        columns: ['y', 'x'],
        values: [
          [1, 2],
          [3, 4],
        ],
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const dataset = await fetchHeatmapDataset('h-live', new AbortController().signal)
    expect(dataset.rows).toEqual(['a', 'b'])
    expect(dataset.columns).toEqual(['x', 'y'])

    const [url] = fetchMock.mock.calls[0] as [string]
    expect(url).toBe(`${API_BASE_URL}/advanced/heatmaps/h-live`)
  })

  it('throws a typed GenomeApiError on non-2xx responses', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 } as unknown as Response)

    await expect(fetchHeatmapDataset('missing')).rejects.toMatchObject({
      name: 'GenomeApiError',
      status: 404,
    })
  })

  it('rethrows an AbortError from an unreadable response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.reject(new DOMException('aborted', 'AbortError')),
    } as unknown as Response)

    await expect(fetchVolcanoDataset('v')).rejects.toMatchObject({ name: 'AbortError' })
  })

  it('throws a GenomeApiError when the payload is invalid', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse({ items: [] }))

    await expect(fetchDistributionDataset('d-bad')).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('normalizes volcano, coverage, and distribution payloads', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          id: 'v-live',
          title: 'V',
          points: [{ identifier: 'g1', effect_size: 1.5, significance: 4 }],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: 'c-live',
          title: 'C',
          bins: [{ chromosome: 'chr1', start: 1, end: 10, coverage: 3 }],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          id: 'd-live',
          title: 'D',
          values: [{ group: 'Tumor', value: 2 }],
        }),
      )

    const volcano = await fetchVolcanoDataset('v-live')
    expect(volcano.points[0]?.effectSize).toBe(1.5)

    const coverage = await fetchCoverageDataset('c-live')
    expect(coverage.bins[0]?.coverage).toBe(3)

    const distribution = await fetchDistributionDataset('d-live')
    expect(distribution.values[0]?.value).toBe(2)
  })
})
