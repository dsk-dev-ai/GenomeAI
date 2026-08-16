import { describe, expect, it } from 'vitest'

import type { CoverageDataset } from './advancedTypes'
import {
  coverageBinTooltip,
  coverageChromosomes,
  coverageDomain,
  coverageExtent,
  hasRenderableBins,
  normalizeCoverageDataset,
  validateCoverageDataset,
} from './coverage'

function dataset(
  bins: CoverageDataset['bins'],
  overrides: Partial<CoverageDataset> = {},
): CoverageDataset {
  return {
    id: 'coverage-test',
    title: 'Test coverage',
    bins,
    ...overrides,
  }
}

function bin(start: number, end: number, coverage = 10, chromosome = 'chr1') {
  return { chromosome, start, end, coverage }
}

describe('validateCoverageDataset', () => {
  it('accepts valid one-based inclusive bins', () => {
    const result = validateCoverageDataset(dataset([bin(1, 10), bin(11, 20)]))
    expect(result.valid).toBe(true)
  })

  it('rejects an empty chromosome', () => {
    const result = validateCoverageDataset(dataset([bin(1, 10, 10, '')]))
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/chromosome/)
  })

  it('rejects non-integer or inverted intervals', () => {
    const result = validateCoverageDataset(dataset([bin(1.5, 10), bin(20, 10)]))
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/interval/)
  })

  it('rejects non-finite coverage', () => {
    const result = validateCoverageDataset(dataset([bin(1, 10, Number.NaN)]))
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/coverage/)
  })
})

describe('normalizeCoverageDataset', () => {
  it('sorts bins by chromosome, start, then end', () => {
    const normalized = normalizeCoverageDataset(
      dataset([bin(20, 30, 1, 'chr2'), bin(1, 10, 1, 'chr1'), bin(2, 3, 1, 'chr1')]),
    )
    expect(normalized.bins.map((entry) => entry.chromosome)).toEqual(['chr1', 'chr1', 'chr2'])
    expect(normalized.bins[0].start).toBe(1)
    expect(normalized.bins[1].start).toBe(2)
  })

  it('dedupes identical intervals keeping the first', () => {
    const normalized = normalizeCoverageDataset(dataset([bin(1, 10, 5), bin(1, 10, 99)]))
    expect(normalized.bins).toHaveLength(1)
    expect(normalized.bins[0].coverage).toBe(5)
  })

  it('drops invalid bins', () => {
    const normalized = normalizeCoverageDataset(dataset([bin(1, 10), bin(20, 10)]))
    expect(normalized.bins).toHaveLength(1)
  })
})

describe('hasRenderableBins / coverageChromosomes', () => {
  it('detects renderable data', () => {
    expect(hasRenderableBins(dataset([]))).toBe(false)
    expect(hasRenderableBins(dataset([bin(1, 10)]))).toBe(true)
  })

  it('returns sorted unique chromosomes', () => {
    expect(
      coverageChromosomes(
        dataset([bin(1, 2, 1, 'chr2'), bin(3, 4, 1, 'chr1'), bin(5, 6, 1, 'chr2')]),
      ),
    ).toEqual(['chr1', 'chr2'])
  })
})

describe('coverageDomain / coverageExtent', () => {
  it('computes the domain for a chromosome only', () => {
    const coverage = dataset([
      bin(1, 10, 5, 'chr1'),
      bin(11, 20, 15, 'chr1'),
      bin(1, 10, 50, 'chr2'),
    ])
    expect(coverageDomain(coverage, 'chr1')).toEqual({ min: 5, max: 15 })
    expect(coverageDomain(coverage, 'chr2')).toEqual({ min: 50, max: 50 })
    expect(coverageDomain(coverage, 'chr3')).toBeUndefined()
  })

  it('computes the extent for a chromosome only', () => {
    const coverage = dataset([bin(5, 10, 1, 'chr1'), bin(1, 100, 1, 'chr2')])
    expect(coverageExtent(coverage, 'chr1')).toEqual({ start: 5, end: 10 })
    expect(coverageExtent(coverage, 'chr2')).toEqual({ start: 1, end: 100 })
  })
})

describe('coverageBinTooltip', () => {
  it('renders the interval and coverage', () => {
    const tooltip = coverageBinTooltip(bin(1, 100, 42.5))
    expect(tooltip.title).toBe('chr1')
    expect(tooltip.subtitle).toBe('1–100')
    expect(tooltip.rows[0]).toEqual({ label: 'Coverage', value: '42.5' })
  })
})
