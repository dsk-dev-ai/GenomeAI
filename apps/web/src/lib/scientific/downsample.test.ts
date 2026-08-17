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

  it('returns the same array when the length exactly matches the limit', () => {
    const items = [1, 2, 3, 4, 5]
    expect(decimateItems(items, 5)).toBe(items)
  })

  it('returns the same (empty) array for an empty input', () => {
    const items: number[] = []
    expect(decimateItems(items, 5)).toBe(items)
  })

  it('returns an empty sample for a negative limit', () => {
    expect(decimateItems([1, 2, 3], -2)).toEqual([])
  })

  it('returns exactly the first element when the limit is one', () => {
    const sampled = decimateItems([1, 2, 3, 4], 1)
    expect([...sampled]).toEqual([1])
  })

  it('returns exactly the first and last elements when the limit is two', () => {
    const sampled = decimateItems([1, 2, 3, 4, 5, 6, 7], 2)
    expect([...sampled]).toEqual([1, 7])
  })

  it('samples odd-sized inputs deterministically with first and last preserved', () => {
    const items = [0, 1, 2, 3, 4, 5, 6]
    const sampled = [...decimateItems(items, 3)]
    expect(sampled[0]).toBe(0)
    expect(sampled[sampled.length - 1]).toBe(6)
    expect(sampled.length).toBeLessThanOrEqual(3)
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

  it('returns the same bins for a non-positive column limit or plot width', () => {
    const bins: CoverageBin[] = [
      { chromosome: 'chr1', start: 1, end: 10, coverage: 5 },
      { chromosome: 'chr1', start: 11, end: 20, coverage: 8 },
    ]
    expect(coverageColumns(bins, toX, 100, 0)).toBe(bins)
    expect(coverageColumns(bins, toX, 0, 50)).toBe(bins)
    expect(coverageColumns(bins, toX, -1, 50)).toBe(bins)
  })

  it('returns the same bins when the count exactly matches the column limit', () => {
    const bins: CoverageBin[] = [
      { chromosome: 'chr1', start: 1, end: 10, coverage: 5 },
      { chromosome: 'chr1', start: 11, end: 20, coverage: 8 },
    ]
    expect(coverageColumns(bins, toX, 100, 2)).toBe(bins)
  })

  it('collapses the whole track into one column carrying the global peak when the limit is one', () => {
    const bins: CoverageBin[] = Array.from({ length: 100 }, (_, index) => ({
      chromosome: 'chr1',
      start: index * 10 + 1,
      end: index * 10 + 10,
      coverage: index % 7,
    }))
    const columns = coverageColumns(bins, toX, 200, 1)
    expect(columns).toHaveLength(1)
    expect(columns[0]?.coverage).toBe(6)
    expect(columns[0]?.start).toBe(1)
    expect(columns[0]?.end).toBe(1000)
  })

  it('merges bins into the span of the whole bucket and keeps the first chromosome', () => {
    const bins: CoverageBin[] = [
      { chromosome: 'chr1', start: 10, end: 20, coverage: 1 },
      { chromosome: 'chr2', start: 30, end: 40, coverage: 5 },
      { chromosome: 'chr1', start: 50, end: 60, coverage: 2 },
    ]
    const columns = coverageColumns(bins, toX, 10, 1)
    expect(columns).toHaveLength(1)
    expect(columns[0]?.start).toBe(10)
    expect(columns[0]?.end).toBe(60)
    expect(columns[0]?.chromosome).toBe('chr1')
  })

  it('returns columns sorted ascending by start', () => {
    const bins: CoverageBin[] = Array.from({ length: 500 }, (_, index) => ({
      chromosome: 'chr1',
      start: index * 5 + 1,
      end: index * 5 + 5,
      coverage: 1,
    }))
    const columns = coverageColumns(bins, toX, 50, 10)
    const starts = columns.map((column) => column.start)
    expect(starts).toEqual([...starts].sort((a, b) => a - b))
  })

  it('clamps bins mapped to negative pixels into the first bucket', () => {
    const toNegative = () => -5
    const bins: CoverageBin[] = Array.from({ length: 8 }, (_, index) => ({
      chromosome: 'chr1',
      start: index * 10 + 1,
      end: index * 10 + 10,
      coverage: index % 4,
    }))
    const columns = coverageColumns(bins, toNegative, 100, 5)
    expect(columns).toHaveLength(1)
    expect(columns[0]?.coverage).toBe(3)
    expect(columns[0]?.start).toBe(1)
    expect(columns[0]?.end).toBe(80)
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

  it('collapses a whole matrix to one block for non-positive limits', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'All',
      rows: ['r1', 'r2', 'r3'],
      columns: ['c1', 'c2', 'c3'],
      values: [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
      ],
    }
    for (const maxRows of [0, -1]) {
      for (const maxCols of [0, -1]) {
        const aggregated = aggregateHeatmap(dataset, maxRows, maxCols)
        expect(aggregated.rows).toEqual(['r1'])
        expect(aggregated.columns).toEqual(['c1'])
        expect(aggregated.values[0]).toEqual([5])
      }
    }
  })

  it('aggregates along a single axis when only the other is oversized', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'ColumnsOnly',
      rows: ['r1', 'r2'],
      columns: ['c1', 'c2', 'c3', 'c4'],
      values: [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
      ],
    }
    const rowsOnly = aggregateHeatmap(dataset, 1, 100)
    expect(rowsOnly.rows).toEqual(['r1'])
    expect(rowsOnly.columns).toEqual(['c1', 'c2', 'c3', 'c4'])
    expect(rowsOnly.values[0]).toEqual([3, 4, 5, 6])

    const colsOnly = aggregateHeatmap(dataset, 100, 2)
    expect(colsOnly.rows).toEqual(['r1', 'r2'])
    expect(colsOnly.columns).toEqual(['c1', 'c3'])
    expect(colsOnly.values[0]).toEqual([1.5, 3.5])
    expect(colsOnly.values[1]).toEqual([5.5, 7.5])
  })

  it('skips NaN and Infinity values when averaging a block', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'NonFinite',
      rows: ['r1', 'r2'],
      columns: ['c1'],
      values: [[Number.NaN], [6]],
    }
    const aggregated = aggregateHeatmap(dataset, 1, 1)
    expect(aggregated.values[0]?.[0]).toBe(6)

    const infinite: HeatmapDataset = {
      id: 'h2',
      title: 'Infinite',
      rows: ['r1', 'r2'],
      columns: ['c1'],
      values: [[Number.POSITIVE_INFINITY], [undefined]],
    }
    const aggregatedInfinite = aggregateHeatmap(infinite, 1, 1)
    expect(aggregatedInfinite.values[0]?.[0]).toBeUndefined()
  })

  it('averages ragged boundary blocks', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'Ragged',
      rows: ['r1', 'r2', 'r3', 'r4', 'r5'],
      columns: ['c1', 'c2', 'c3', 'c4', 'c5'],
      values: Array.from({ length: 5 }, (_, r) =>
        Array.from({ length: 5 }, (_, c) => r * 5 + c + 1),
      ),
    }
    const aggregated = aggregateHeatmap(dataset, 2, 2)
    // Block size ceil(5/2) = 3, so rows/columns sample at indices 0 and 3.
    expect(aggregated.rows).toEqual(['r1', 'r4'])
    expect(aggregated.columns).toEqual(['c1', 'c4'])
    // Bottom-right block spans rows r4..r5, columns c4..c5: mean(19,20,24,25) = 22.
    expect(aggregated.values[1]?.[1]).toBe(22)
  })

  it('tolerates ragged rows with missing value arrays', () => {
    const dataset: HeatmapDataset = {
      id: 'h',
      title: 'MissingRow',
      rows: ['r1', 'r2'],
      columns: ['c1', 'c2'],
      values: [[1, 2], undefined],
    } as HeatmapDataset
    const aggregated = aggregateHeatmap(dataset, 1, 1)
    expect(aggregated.values[0]?.[0]).toBe(1.5)
  })

  it('propagates id, title, labels, and metadata through aggregation', () => {
    const dataset: HeatmapDataset = {
      id: 'h-id',
      title: 'Named',
      rows: ['r1', 'r2'],
      columns: ['c1', 'c2'],
      values: [
        [1, 2],
        [3, 4],
      ],
      rowLabels: { r1: 'Row One' },
      columnLabels: { c1: 'Col One' },
      metadata: { source: 'fixture' },
    }
    const aggregated = aggregateHeatmap(dataset, 1, 1)
    expect(aggregated.id).toBe('h-id')
    expect(aggregated.title).toBe('Named')
    expect(aggregated.rowLabels).toEqual({ r1: 'Row One' })
    expect(aggregated.columnLabels).toEqual({ c1: 'Col One' })
    expect(aggregated.metadata).toEqual({ source: 'fixture' })
  })
})
