import { describe, expect, it } from 'vitest'

import {
  availableSamples,
  datasetDomain,
  expressionValueDomain,
  hasNormalizedValues,
  hasRenderablePoints,
  normalizeExpressionDataset,
  sanitizeMetadata,
  seriesDomain,
  validateExpressionDataset,
  validateExpressionPoint,
} from './expression'
import type { ExpressionDataset } from './types'

function dataset(series: ExpressionDataset['series']): ExpressionDataset {
  return { id: 'd', title: 'Dataset', series }
}

function point(identifier: string, sample: string, value: number, normalizedValue?: number) {
  return {
    identifier,
    sample,
    value,
    ...(normalizedValue !== undefined ? { normalizedValue } : {}),
  }
}

describe('validateExpressionPoint', () => {
  it('accepts a valid point', () => {
    expect(validateExpressionPoint(point('TP53', 'Tumor-1', 128.4), 0, 'tp53')).toEqual([])
  })

  it('rejects missing identifier, sample, and non-finite values', () => {
    expect(validateExpressionPoint(point('', 'Tumor-1', 1), 0, 's')).toHaveLength(1)
    expect(validateExpressionPoint(point('TP53', '', 1), 0, 's')).toHaveLength(1)
    expect(validateExpressionPoint(point('TP53', 'Tumor-1', Number.NaN), 0, 's')).toHaveLength(1)
    expect(
      validateExpressionPoint(
        { identifier: 'TP53', sample: 'Tumor-1', value: 1, normalizedValue: Number.NaN },
        0,
        's',
      ),
    ).toHaveLength(1)
  })

  it('accepts zero and negative values', () => {
    expect(validateExpressionPoint(point('TP53', 'Tumor-1', 0), 0, 's')).toEqual([])
    expect(validateExpressionPoint(point('TP53', 'Tumor-1', -1.5), 0, 's')).toEqual([])
  })
})

describe('validateExpressionDataset', () => {
  it('reports every problem and passes on clean data', () => {
    const bad = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [point('TP53', 'Tumor-1', 1), point('', 'Tumor-1', Number.NaN)],
      },
      { id: 's1', label: '', points: [] },
    ])
    const validation = validateExpressionDataset(bad)
    expect(validation.valid).toBe(false)
    expect(validation.errors.length).toBeGreaterThanOrEqual(4)

    const clean = dataset([{ id: 's1', label: 'S1', points: [point('TP53', 'Tumor-1', 1)] }])
    expect(validateExpressionDataset(clean)).toEqual({ valid: true, errors: [] })
  })

  it('flags duplicate series ids', () => {
    const duplicate = dataset([
      { id: 's1', label: 'A', points: [] },
      { id: 's1', label: 'B', points: [] },
    ])
    const validation = validateExpressionDataset(duplicate)
    expect(validation.valid).toBe(false)
    expect(validation.errors.some((error) => error.includes('Duplicate series id'))).toBe(true)
  })
})

describe('normalizeExpressionDataset', () => {
  it('orders series by id and points by sample then identifier', () => {
    const input = dataset([
      {
        id: 'b',
        label: 'B',
        points: [point('X', 'Tumor-2', 1), point('X', 'Tumor-1', 2), point('A', 'Tumor-1', 3)],
      },
      { id: 'a', label: 'A', points: [point('X', 'Normal-1', 4)] },
    ])
    const normalized = normalizeExpressionDataset(input)
    expect(normalized.series.map((series) => series.id)).toEqual(['a', 'b'])
    expect(normalized.series[1].points.map((p) => [p.sample, p.identifier])).toEqual([
      ['Tumor-1', 'A'],
      ['Tumor-1', 'X'],
      ['Tumor-2', 'X'],
    ])
  })

  it('drops invalid points and dedupes duplicate identifiers (first wins)', () => {
    const input = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [
          point('TP53', 'Tumor-1', 10),
          point('TP53', 'Tumor-1', 99),
          point('', 'Tumor-1', 5),
          point('X', '', 5),
          point('Y', 'Tumor-1', Number.NaN),
        ],
      },
    ])
    const normalized = normalizeExpressionDataset(input)
    expect(normalized.series[0].points).toHaveLength(1)
    expect(normalized.series[0].points[0].value).toBe(10)
  })

  it('drops series without an id or label', () => {
    const input = dataset([
      { id: '', label: 'S1', points: [point('TP53', 'Tumor-1', 1)] },
      { id: 'keep', label: 'S2', points: [point('TP53', 'Tumor-1', 1)] },
    ])
    expect(normalizeExpressionDataset(input).series.map((s) => s.id)).toEqual(['keep'])
  })

  it('dedupes series with the same id, keeping the first occurrence', () => {
    const input = dataset([
      { id: 'dup', label: 'First', points: [point('A', 'Tumor-1', 1)] },
      { id: 'dup', label: 'Second', points: [point('B', 'Tumor-1', 2)] },
      { id: 'keep', label: 'Keep', points: [point('C', 'Tumor-1', 3)] },
    ])
    const normalized = normalizeExpressionDataset(input)
    expect(normalized.series.map((s) => s.id)).toEqual(['dup', 'keep'])
    expect(normalized.series[0].label).toBe('First')
    expect(validateExpressionDataset(normalized).valid).toBe(true)
  })

  it('sorts with locale-independent code-unit order', () => {
    // In most collation locales 'ä' sorts as "a" (before 'z'); code-unit order
    // places 'z' (0x7A) before 'ä' (0xE4). LocaleCompare would put 'ä' first.
    const input = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [point('X', 'ä', 1), point('X', 'z', 2), point('X', 'Z', 3)],
      },
    ])
    const normalized = normalizeExpressionDataset(input)
    const samples = normalized.series[0].points.map((p) => p.sample)
    expect(samples).toEqual(['Z', 'z', 'ä'])
    expect(availableSamples(input)).toEqual(['Z', 'z', 'ä'])
  })

  it('does not share mutable state with the input', () => {
    const point = { identifier: 'TP53', sample: 'Tumor-1', value: 10, metadata: { status: 'on' } }
    const input = dataset([{ id: 's1', label: 'S1', points: [point] }])
    const normalized = normalizeExpressionDataset(input)

    point.value = 999
    point.metadata.status = 'off'
    point.identifier = 'mutated'
    input.series[0].label = 'Mutated'
    input.metadata = { mutated: true }

    const normalizedPoint = normalized.series[0].points[0]
    expect(normalizedPoint.value).toBe(10)
    expect(normalizedPoint.identifier).toBe('TP53')
    expect(normalizedPoint.metadata?.status).toBe('on')
    expect(normalized.series[0].label).toBe('S1')
  })

  it('falls back to defaults for empty ids and titles', () => {
    const input = dataset([])
    const empty = normalizeExpressionDataset({ ...input, id: '', title: '' })
    expect(empty.id).toBe('unnamed-dataset')
    expect(empty.title).toBe('Unnamed dataset')
  })
})

describe('availableSamples', () => {
  it('returns the sorted unique sample names', () => {
    const input = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [point('A', 'Tumor-2', 1), point('A', 'Tumor-1', 2), point('B', 'Tumor-2', 3)],
      },
    ])
    expect(availableSamples(input)).toEqual(['Tumor-1', 'Tumor-2'])
  })

  it('returns an empty array for empty data', () => {
    expect(availableSamples(dataset([]))).toEqual([])
  })
})

describe('seriesDomain and datasetDomain', () => {
  it('computes min/max across points, skipping non-finite values', () => {
    const series = {
      id: 's1',
      label: 'S1',
      points: [
        point('A', 'Tumor-1', 2),
        point('B', 'Tumor-1', 8),
        point('C', 'Tumor-1', Number.NaN),
        point('D', 'Tumor-1', 0),
      ],
    }
    expect(seriesDomain(series, 'value')).toEqual({ min: 0, max: 8 })
  })

  it('aggregates across series and uses the normalized field', () => {
    const input = dataset([
      { id: 's1', label: 'S1', points: [point('A', 'Tumor-1', 5, 1.2)] },
      { id: 's2', label: 'S2', points: [point('A', 'Tumor-1', 5, -0.7)] },
    ])
    expect(datasetDomain(input, 'value')).toEqual({ min: 5, max: 5 })
    expect(datasetDomain(input, 'normalizedValue')).toEqual({ min: -0.7, max: 1.2 })
  })

  it('returns undefined when no usable points exist', () => {
    expect(datasetDomain(dataset([]), 'value')).toBeUndefined()
    expect(datasetDomain(dataset([{ id: 's1', label: 'S1', points: [] }]), 'value')).toBeUndefined()
  })
})

describe('expressionValueDomain', () => {
  it('starts all-non-negative domains at zero', () => {
    const input = dataset([{ id: 's1', label: 'S1', points: [point('A', 'Tumor-1', 44.2)] }])
    expect(expressionValueDomain(input, 'value')).toEqual({ min: 0, max: 44.2 })
  })

  it('ends all-negative domains at zero', () => {
    const input = dataset([{ id: 's1', label: 'S1', points: [point('A', 'Tumor-1', -2.5)] }])
    expect(expressionValueDomain(input, 'value')).toEqual({ min: -2.5, max: 0 })
  })

  it('uses the raw span for mixed-sign data', () => {
    const input = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [point('A', 'Tumor-1', -3, -3), point('B', 'Tumor-1', 2, 2)],
      },
    ])
    expect(expressionValueDomain(input, 'normalizedValue')).toEqual({ min: -3, max: 2 })
  })

  it('pads degenerate single-value datasets', () => {
    const input = dataset([{ id: 's1', label: 'S1', points: [point('A', 'Tumor-1', 10)] }])
    const domain = expressionValueDomain(input, 'value')
    expect(domain.max).toBeGreaterThan(domain.min)
  })

  it('returns a safe default for empty data', () => {
    expect(expressionValueDomain(dataset([]), 'value')).toEqual({ min: 0, max: 1 })
  })
})

describe('hasRenderablePoints and hasNormalizedValues', () => {
  it('detects renderable points and normalized values', () => {
    const input = dataset([
      {
        id: 's1',
        label: 'S1',
        points: [point('A', 'Tumor-1', 1, 2), point('B', 'Tumor-2', Number.NaN)],
      },
    ])
    expect(hasRenderablePoints(input)).toBe(true)
    expect(hasNormalizedValues(input)).toBe(true)
  })

  it('returns false for empty or invalid data', () => {
    expect(hasRenderablePoints(dataset([]))).toBe(false)
    expect(hasNormalizedValues(dataset([{ id: 's1', label: 'S1', points: [] }]))).toBe(false)
  })
})

describe('sanitizeMetadata', () => {
  it('keeps scalar entries and drops non-scalar ones', () => {
    expect(sanitizeMetadata({ status: 'over', count: 2, nested: { a: 1 }, list: [1] })).toEqual({
      status: 'over',
      count: 2,
    })
  })

  it('returns undefined for invalid input', () => {
    expect(sanitizeMetadata(null)).toBeUndefined()
    expect(sanitizeMetadata([1])).toBeUndefined()
    expect(sanitizeMetadata('x')).toBeUndefined()
  })
})
