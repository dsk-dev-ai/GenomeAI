import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_PATHWAY_HEATMAP_FIXTURE } from './advanced.fixtures'
import {
  coverageFromRecords,
  distributionFromRecords,
  heatmapFromRecords,
  toCoverageBin,
  toDistributionValue,
  toVolcanoPoint,
  volcanoFromRecords,
} from './advancedApi'

afterEach(() => {
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
