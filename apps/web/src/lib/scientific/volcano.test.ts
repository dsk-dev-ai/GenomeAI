import { describe, expect, it } from 'vitest'

import type { VolcanoDataset } from './advancedTypes'
import {
  hasRenderablePoints,
  isVolcanoHighlighted,
  normalizeVolcanoDataset,
  validateVolcanoDataset,
  volcanoDomains,
  volcanoPointTooltip,
} from './volcano'

function dataset(
  points: VolcanoDataset['points'],
  overrides: Partial<VolcanoDataset> = {},
): VolcanoDataset {
  return {
    id: 'volcano-test',
    title: 'Test volcano',
    points,
    ...overrides,
  }
}

describe('validateVolcanoDataset', () => {
  it('accepts valid points', () => {
    const result = validateVolcanoDataset(
      dataset([{ identifier: 'g1', effectSize: 1.2, significance: 4 }]),
    )
    expect(result.valid).toBe(true)
  })

  it('rejects empty identifiers', () => {
    const result = validateVolcanoDataset(
      dataset([{ identifier: '', effectSize: 1, significance: 4 }]),
    )
    expect(result.valid).toBe(false)
  })

  it('rejects non-finite effect sizes or significance', () => {
    const result = validateVolcanoDataset(
      dataset([{ identifier: 'g1', effectSize: Number.NaN, significance: 4 }]),
    )
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/effectSize/)
  })

  it('rejects non-finite adjusted significance', () => {
    const result = validateVolcanoDataset(
      dataset([
        { identifier: 'g1', effectSize: 1, significance: 4, adjustedSignificance: Number.NaN },
      ]),
    )
    expect(result.valid).toBe(false)
  })
})

describe('normalizeVolcanoDataset', () => {
  it('sorts points canonically by identifier', () => {
    const normalized = normalizeVolcanoDataset(
      dataset([
        { identifier: 'z', effectSize: 1, significance: 1 },
        { identifier: 'a', effectSize: 1, significance: 1 },
      ]),
    )
    expect(normalized.points.map((point) => point.identifier)).toEqual(['a', 'z'])
  })

  it('drops invalid points and dedupes duplicate identifiers', () => {
    const normalized = normalizeVolcanoDataset(
      dataset([
        { identifier: 'g1', effectSize: 1, significance: 1 },
        { identifier: '', effectSize: 1, significance: 1 },
        { identifier: 'g2', effectSize: Number.NaN, significance: 1 },
        { identifier: 'g1', effectSize: 99, significance: 99 },
      ]),
    )
    expect(normalized.points).toHaveLength(1)
    expect(normalized.points[0].effectSize).toBe(1)
  })

  it('never mutates the input', () => {
    const input = dataset([{ identifier: 'g1', effectSize: 1, significance: 1 }])
    normalizeVolcanoDataset(input)
    expect(input.points).toHaveLength(1)
  })
})

describe('hasRenderablePoints', () => {
  it('is false for an empty dataset', () => {
    expect(hasRenderablePoints(dataset([]))).toBe(false)
  })

  it('is true with at least one point', () => {
    expect(
      hasRenderablePoints(dataset([{ identifier: 'g1', effectSize: 1, significance: 1 }])),
    ).toBe(true)
  })
})

describe('volcanoDomains', () => {
  it('derives effect-size and significance domains', () => {
    const domains = volcanoDomains(
      dataset([
        { identifier: 'a', effectSize: -2, significance: 1 },
        { identifier: 'b', effectSize: 3, significance: 5 },
      ]),
    )
    expect(domains?.effectSize).toEqual({ min: -2, max: 3 })
    expect(domains?.significance).toEqual({ min: 0, max: 5 })
  })

  it('symmetrizes single-signed effect sizes around zero', () => {
    const domains = volcanoDomains(dataset([{ identifier: 'a', effectSize: 2, significance: 1 }]))
    expect(domains?.effectSize).toEqual({ min: -2, max: 2 })
  })

  it('returns undefined for an empty dataset', () => {
    expect(volcanoDomains(dataset([]))).toBeUndefined()
  })
})

describe('isVolcanoHighlighted', () => {
  const point = { identifier: 'g1', effectSize: 1.5, significance: 3 }

  it('highlights points above both thresholds', () => {
    expect(isVolcanoHighlighted(point, { effectThreshold: 1, significanceThreshold: 2 })).toBe(true)
  })

  it('does not highlight when below either threshold', () => {
    expect(isVolcanoHighlighted(point, { effectThreshold: 2, significanceThreshold: 2 })).toBe(
      false,
    )
    expect(isVolcanoHighlighted(point, { effectThreshold: 1, significanceThreshold: 4 })).toBe(
      false,
    )
  })

  it('uses zero thresholds by default', () => {
    expect(isVolcanoHighlighted({ ...point, effectSize: 0.1, significance: 0.1 })).toBe(true)
  })
})

describe('volcanoPointTooltip', () => {
  it('renders the identifier, effect size, and significance', () => {
    const tooltip = volcanoPointTooltip({ identifier: 'g1', effectSize: 1.25, significance: 3.5 })
    expect(tooltip.title).toBe('g1')
    expect(tooltip.rows[0]).toEqual({ label: 'Effect size', value: '1.25' })
    expect(tooltip.rows[1]).toEqual({ label: 'Significance', value: '3.5' })
  })

  it('includes adjusted significance when present', () => {
    const tooltip = volcanoPointTooltip({
      identifier: 'g1',
      effectSize: 1,
      significance: 2,
      adjustedSignificance: 1.5,
    })
    expect(tooltip.rows.map((row) => row.label)).toContain('Adjusted significance')
  })

  it('includes metadata rows', () => {
    const tooltip = volcanoPointTooltip({
      identifier: 'g1',
      effectSize: 1,
      significance: 2,
      metadata: { status: 'up' },
    })
    expect(tooltip.rows.map((row) => row.label)).toContain('status')
  })
})
