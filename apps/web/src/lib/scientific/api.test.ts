import { afterEach, describe, expect, it, vi } from 'vitest'

import { GenomeApiError } from '@/lib/genome/api'

import {
  expressionDatasetFromRecords,
  fetchExpressionDataset,
  toExpressionPoint,
  toExpressionSeries,
} from './api'
import { validateExpressionDataset } from './expression'
import { availableSamples } from './expression'
import { TP53_PATHWAY_EXPRESSION_FIXTURE, buildExpressionDataset } from './expression.fixtures'

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

describe('toExpressionPoint', () => {
  it('normalizes a raw point record', () => {
    const point = toExpressionPoint({
      identifier: 'TP53',
      sample: 'Tumor-1',
      value: 128.4,
      normalized_value: 1.92,
      metadata: { status: 'overexpressed' },
    })
    expect(point?.identifier).toBe('TP53')
    expect(point?.sample).toBe('Tumor-1')
    expect(point?.value).toBe(128.4)
    expect(point?.normalizedValue).toBe(1.92)
    expect(point?.metadata?.status).toBe('overexpressed')
  })

  it('accepts the camelCase normalized field', () => {
    expect(
      toExpressionPoint({ identifier: 'A', sample: 'S', value: 1, normalizedValue: 2 })
        ?.normalizedValue,
    ).toBe(2)
  })

  it('drops records missing required fields or with non-finite values', () => {
    expect(toExpressionPoint({ sample: 'S', value: 1 })).toBeUndefined()
    expect(toExpressionPoint({ identifier: 'A', value: 1 })).toBeUndefined()
    expect(toExpressionPoint({ identifier: 'A', sample: 'S', value: Number.NaN })).toBeUndefined()
    expect(toExpressionPoint(null)).toBeUndefined()
  })
})

describe('toExpressionSeries', () => {
  it('normalizes a raw series record', () => {
    const series = toExpressionSeries({
      id: 'tp53',
      label: 'TP53',
      points: [{ identifier: 'TP53', sample: 'Tumor-1', value: 10 }],
    })
    expect(series?.id).toBe('tp53')
    expect(series?.label).toBe('TP53')
    expect(series?.points).toHaveLength(1)
  })

  it('drops invalid points and series without id/label', () => {
    const series = toExpressionSeries({
      id: 's1',
      label: 'S1',
      points: [
        { identifier: 'A', sample: 'Tumor-1', value: 1 },
        { sample: 'x', value: 1 },
      ],
    })
    expect(series?.points).toHaveLength(1)
    expect(toExpressionSeries({ label: 'S1', points: [] })).toBeUndefined()
    expect(toExpressionSeries(null)).toBeUndefined()
  })
})

describe('expressionDatasetFromRecords', () => {
  it('builds a normalized valid dataset', () => {
    const data = expressionDatasetFromRecords({
      id: 'd1',
      title: 'Title',
      series: [
        { id: 's1', label: 'S1', points: [{ identifier: 'A', sample: 'Tumor-1', value: 1 }] },
      ],
    })
    expect(data?.id).toBe('d1')
    expect(data?.title).toBe('Title')
    if (data !== undefined) expect(validateExpressionDataset(data).valid).toBe(true)
  })

  it('returns undefined for invalid records', () => {
    expect(expressionDatasetFromRecords(null)).toBeUndefined()
    expect(expressionDatasetFromRecords({ series: [] })).toBeUndefined()
  })
})

describe('fetchExpressionDataset', () => {
  it('GETs the expression endpoint and normalizes the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: 'expression-tp53-pathway',
        series: [
          {
            id: 'tp53',
            label: 'TP53',
            points: [{ identifier: 'TP53', sample: 'Tumor-1', value: 128.4 }],
          },
        ],
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const data = await fetchExpressionDataset('expression-tp53-pathway', signal)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/expression/datasets/expression-tp53-pathway')
    expect(init.signal).toBe(signal)
    expect(data.id).toBe('expression-tp53-pathway')
    expect(data.series).toHaveLength(1)
  })

  it('throws a GenomeApiError on a non-2xx response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 } as unknown as Response)
    await expect(fetchExpressionDataset('d1')).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('throws a GenomeApiError when the response body is not JSON', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.reject(new SyntaxError('Unexpected token < in JSON')),
    } as unknown as Response)
    await expect(fetchExpressionDataset('d1')).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('rethrows an abort error instead of converting it to a GenomeApiError', async () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError')
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.reject(abortError),
    } as unknown as Response)
    await expect(fetchExpressionDataset('d1')).rejects.toBe(abortError)
  })

  it('throws a GenomeApiError on a malformed payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(null))
    await expect(fetchExpressionDataset('d1')).rejects.toBeInstanceOf(GenomeApiError)
  })
})

describe('fixture integrity', () => {
  it('fixture flows through the same normalizers', () => {
    expect(TP53_PATHWAY_EXPRESSION_FIXTURE.id).toBe('expression-tp53-pathway')
    expect(validateExpressionDataset(TP53_PATHWAY_EXPRESSION_FIXTURE).valid).toBe(true)
    expect(TP53_PATHWAY_EXPRESSION_FIXTURE.series).toHaveLength(3)
  })

  it('buildExpressionDataset produces valid datasets for edge cases', () => {
    const single = buildExpressionDataset({
      series: [{ id: 's1', label: 'S1', points: [['Tumor-1', 1]] }],
    })
    expect(validateExpressionDataset(single).valid).toBe(true)
    expect(availableSamples(single)).toEqual(['Tumor-1'])
  })
})
