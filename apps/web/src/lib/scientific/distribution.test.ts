import { describe, expect, it } from 'vitest'

import type { DistributionDataset } from './advancedTypes'
import {
  distributionGroups,
  distributionTooltip,
  groupStatistics,
  groupWhiskers,
  hasRenderableValues,
  normalizeDistributionDataset,
  validateDistributionDataset,
  valuesForGroup,
} from './distribution'

function dataset(
  values: DistributionDataset['values'],
  overrides: Partial<DistributionDataset> = {},
): DistributionDataset {
  return {
    id: 'distribution-test',
    title: 'Test distribution',
    values,
    ...overrides,
  }
}

function value(group: string, value: number) {
  return { group, value }
}

describe('validateDistributionDataset', () => {
  it('accepts valid grouped values', () => {
    const result = validateDistributionDataset(dataset([value('Tumor', 1), value('Normal', 2)]))
    expect(result.valid).toBe(true)
  })

  it('rejects empty groups', () => {
    const result = validateDistributionDataset(dataset([value('', 1)]))
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/group/)
  })

  it('rejects non-finite values', () => {
    const result = validateDistributionDataset(dataset([value('Tumor', Number.NaN)]))
    expect(result.valid).toBe(false)
  })
})

describe('normalizeDistributionDataset', () => {
  it('sorts values by group then ascending value', () => {
    const normalized = normalizeDistributionDataset(
      dataset([value('Tumor', 3), value('Normal', 2), value('Tumor', 1)]),
    )
    expect(normalized.values.map((entry) => `${entry.group}:${entry.value}`)).toEqual([
      'Normal:2',
      'Tumor:1',
      'Tumor:3',
    ])
  })

  it('drops invalid values', () => {
    const normalized = normalizeDistributionDataset(
      dataset([value('Tumor', 1), value('', 2), value('Normal', Number.NaN)]),
    )
    expect(normalized.values).toHaveLength(1)
  })
})

describe('distributionGroups / valuesForGroup', () => {
  it('returns sorted unique groups', () => {
    const data = dataset([value('Tumor', 1), value('Normal', 2), value('Tumor', 3)])
    expect(distributionGroups(data)).toEqual(['Normal', 'Tumor'])
  })

  it('returns the values belonging to a group', () => {
    const data = dataset([value('Tumor', 1), value('Normal', 2), value('Tumor', 3)])
    expect(valuesForGroup(data, 'Tumor')).toEqual([1, 3])
  })
})

describe('groupStatistics / groupWhiskers', () => {
  it('computes per-group summary statistics', () => {
    const data = dataset([
      value('Tumor', 1),
      value('Tumor', 2),
      value('Tumor', 3),
      value('Normal', 100),
    ])
    const summary = groupStatistics(data, 'Tumor')
    expect(summary?.count).toBe(3)
    expect(summary?.mean).toBe(2)
    expect(summary?.q2).toBe(2)
    expect(groupStatistics(data, 'Missing')).toBeUndefined()
  })

  it('computes per-group whiskers', () => {
    const data = dataset([
      value('Tumor', 1),
      value('Tumor', 2),
      value('Tumor', 3),
      value('Tumor', 100),
    ])
    const whiskers = groupWhiskers(data, 'Tumor')
    expect(whiskers?.upper).toBe(3)
    expect(whiskers?.outliers).toEqual([100])
  })
})

describe('hasRenderableValues / distributionTooltip', () => {
  it('detects renderable data', () => {
    expect(hasRenderableValues(dataset([]))).toBe(false)
    expect(hasRenderableValues(dataset([value('Tumor', 1)]))).toBe(true)
  })

  it('builds a tooltip with summary rows', () => {
    const data = dataset([value('Tumor', 1), value('Tumor', 2), value('Tumor', 3)])
    const tooltip = distributionTooltip(data, 'Tumor')
    expect(tooltip.title).toBe('Tumor')
    expect(tooltip.rows[0]).toEqual({ label: 'Count', value: '3' })
    expect(tooltip.rows[1]).toEqual({ label: 'Mean', value: '2' })
    expect(tooltip.rows[2]).toEqual({ label: 'Median', value: '2' })
  })
})
