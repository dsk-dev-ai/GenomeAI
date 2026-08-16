import { describe, expect, it } from 'vitest'

import { boxPlotWhiskers, quantile, sortedSample, summarize } from './statistics'

describe('sortedSample', () => {
  it('returns finite values ascending without mutating the input', () => {
    const input = [3, 1, 2]
    const result = sortedSample(input)
    expect(result).toEqual([1, 2, 3])
    expect(input).toEqual([3, 1, 2])
  })

  it('drops non-finite values', () => {
    expect(sortedSample([Number.NaN, 2, Number.POSITIVE_INFINITY, 1])).toEqual([1, 2])
  })

  it('returns an empty array for an empty sample', () => {
    expect(sortedSample([])).toEqual([])
  })
})

describe('quantile', () => {
  it('returns the exact median for an odd-sized sorted sample', () => {
    expect(quantile([1, 2, 3, 4, 5], 0.5)).toBe(3)
  })

  it('interpolates between the two middle values for an even sample', () => {
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5)
  })

  it('returns min/max for q=0 and q=1', () => {
    expect(quantile([1, 2, 3], 0)).toBe(1)
    expect(quantile([1, 2, 3], 1)).toBe(3)
  })

  it('clamps out-of-range quantiles', () => {
    expect(quantile([1, 2, 3], -1)).toBe(1)
    expect(quantile([1, 2, 3], 2)).toBe(3)
  })

  it('returns NaN for an empty sample', () => {
    expect(quantile([], 0.5)).toBeNaN()
  })
})

describe('summarize', () => {
  it('computes summary statistics for a sample', () => {
    const summary = summarize([1, 2, 3, 4, 5])
    expect(summary).toEqual({
      count: 5,
      mean: 3,
      min: 1,
      max: 5,
      q1: 2,
      q2: 3,
      q3: 4,
      iqr: 2,
    })
  })

  it('returns undefined for an empty sample', () => {
    expect(summarize([])).toBeUndefined()
  })
})

describe('boxPlotWhiskers', () => {
  it('computes whiskers within 1.5 * IQR and reports outliers', () => {
    // Values 1..10; IQR spans 3..8 (q1=3, q3=8, iqr=5).
    const whiskers = boxPlotWhiskers([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    expect(whiskers).toBeDefined()
    expect(whiskers?.lower).toBe(1)
    expect(whiskers?.upper).toBe(10)
    expect(whiskers?.outliers).toEqual([])
  })

  it('flags values beyond 1.5 * IQR as outliers', () => {
    const whiskers = boxPlotWhiskers([1, 2, 3, 4, 5, 6, 7, 8, 100])
    expect(whiskers?.upper).toBe(8)
    expect(whiskers?.outliers).toEqual([100])
  })

  it('returns undefined for an empty sample', () => {
    expect(boxPlotWhiskers([])).toBeUndefined()
  })
})
