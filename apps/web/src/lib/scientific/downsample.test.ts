import { describe, expect, it } from 'vitest'

import type { CoverageBin, HeatmapDataset } from './advancedTypes'
import { aggregateHeatmap, coverageColumns, decimateItems } from './downsample'

describe('decimateItems', () => {
  it('returns the same array when the input already fits', () => {
    const input = [1, 2, 3, 4]
    expect(decimateItems(input, 10)).toBe(input)
  })

  it('returns an empty sample for a non-positive limit', () => {
    expect(decimateItems([1, 2, 3], 0)).toEqual([])
  })

  it('never exceeds the requested count', () => {
    const items = Array.from({ length: 10_000 }, (_, index) => index)
    expect(decimateItems(items, 100).length).toBeLessThanOrEqual(100)
  })

  it('always preserves the first and last elements', () => {
    const items = Array.from({ length: 500 }, (_, index) => index)
    const sampled = decimateItems(items, 50)
    expect(sampled[0]).toBe(items[0])
    expect(sampled[sampled.length - 1]).toBe(items[items.length - 1])
  })

  it('is deterministic for a given input', () => {
    const items = Array.from({ length: 1234 }, (_, index) => index)
    expect(decimateItems(items, 100)).toEqual(decimateItems(items, 100))
  })

  it('returns a strict in-order subset when decimating', () => {
    const items = Array.from({ length: 300 }, (_, index) => index)
    const sampled = [...decimateItems(items, 10)]
    expect(sampled.length).toBeLessThan(items.length)
    expect(sampled).toEqual([...sampled].sort((a, b) => a - b))
  })
})

describe('coverageColumns', () => {
  const toX = (base: number) => (base - 1) * 1

  it('returns the same bins when the count already fits', () => {
    const bins: CoverageBin[] = [
      { chromosome: 'chr1', start: 1, end: 10, coverage: 5 },
      { chromosome: 'chr1', start: 11, end: 20, coverage: 8 },
    ]
    expect(coverageColumns(bins, toX, 100, 50)).toBe(bins)
  })

  it('returns the same bins for an empty input', () => {
    const bins: CoverageBin[] = []
    expect(coverageColumns(bins, toX, 100, 50)).toBe(bins)
  })

  it('aggregates into at most the requested number of columns', () => {
    const bins: CoverageBin[] = Array.from({ length: 5000 }, (_, index) => ({
      chromosome: 'chr1',
      start: index * 10 + 1,
      end: index * 10 + 10,
      coverage: (index % 7) + 1,
    }))
    const columns = coverageColumns(bins, toX, 200, 100)
    expect(columns.length).toBeLessThanOrEqual(100)
  })

  it('preserves the peak coverage within each column', () => {
    const plotWidth = 200
    const maxColumns = 50
    const bucket = (base: number) =>
      Math.min(maxColumns - 1, Math.max(0, Math.floor((toX(base) / plotWidth) * maxColumns)))
    const bins: CoverageBin[] = Array.from({ length: 5000 }, (_, index) => ({
      chromosome: 'chr1',
      start: index * 2 + 1,
      end: index * 2 + 2,
      coverage: index,
    }))
    const columns = coverageColumns(bins, toX, plotWidth, maxColumns)
    for (const column of columns) {
      const merged = bins.filter((bin) => bucket(bin.start) === bucket(column.start))
      const expectedMax =
        merged.length > 0 ? Math.max(...merged.map((bin) => bin.coverage)) : undefined
      if (expectedMax !== undefined) {
        expect(column.coverage).toBe(expectedMax)
      }
    }
  })

  it('is deterministic for a given input', () => {
    const bins: CoverageBin[] = Array.from({ length: 4000 }, (_, index) => ({
      chromosome: 'chr1',
      start: index + 1,
      end: index + 1,
      coverage: index % 9,
    }))
    expect(coverageColumns(bins, toX, 300, 80)).toEqual(coverageColumns(bins, toX, 300, 80))
  })
})

describe('aggregateHeatmap', () => {
  it('returns the same dataset when the matrix already fits', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'Small',
      rows: ['r1', 'r2'],
      columns: ['c1'],
      values: [[1], [2]],
    }
    expect(aggregateHeatmap(dataset, 10, 10)).toBe(dataset)
  })

  it('bounds the aggregated rows and columns', () => {
    const rows = Array.from({ length: 400 }, (_, index) => `r${index}`)
    const columns = Array.from({ length: 300 }, (_, index) => `c${index}`)
    const values = rows.map(() => columns.map(() => 1))
    const dataset: HeatmapDataset = { id: 'h', title: 'Big', rows, columns, values }
    const aggregated = aggregateHeatmap(dataset, 50, 40)
    expect(aggregated.rows.length).toBeLessThanOrEqual(50)
    expect(aggregated.columns.length).toBeLessThanOrEqual(40)
    expect(aggregated.values.length).toBe(aggregated.rows.length)
    for (const row of aggregated.values) {
      expect(row.length).toBe(aggregated.columns.length)
    }
  })

  it('block-averages finite values', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'Blocks',
      rows: ['r1', 'r2', 'r3', 'r4'],
      columns: ['c1', 'c2', 'c3', 'c4'],
      values: [
        [1, 2, 5, 6],
        [3, 4, 7, 8],
        [9, 10, 13, 14],
        [11, 12, 15, 16],
      ],
    }
    const aggregated = aggregateHeatmap(dataset, 2, 2)
    expect(aggregated.rows).toEqual(['r1', 'r3'])
    expect(aggregated.columns).toEqual(['c1', 'c3'])
    // Top-left block: mean(1,2,3,4) = 2.5; top-right: mean(5,6,7,8) = 6.5
    expect(aggregated.values[0]?.[0]).toBe(2.5)
    expect(aggregated.values[0]?.[1]).toBe(6.5)
    // Bottom-left block: mean(9,10,11,12) = 10.5; bottom-right: mean(13..16) = 14.5
    expect(aggregated.values[1]?.[0]).toBe(10.5)
    expect(aggregated.values[1]?.[1]).toBe(14.5)
  })

  it('keeps missing blocks missing and averages over finite values only', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'Missing',
      rows: ['r1', 'r2'],
      columns: ['c1', 'c2'],
      values: [
        [undefined, undefined],
        [1, 3],
      ],
    }
    const aggregated = aggregateHeatmap(dataset, 1, 1)
    // Whole matrix collapses to one block; finite values are 1 and 3.
    expect(aggregated.values[0]?.[0]).toBe(2)
  })
})
