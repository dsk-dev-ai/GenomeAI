/**
 * Deterministic downsampling and aggregation for large scientific datasets
 * (Phase 6 — Visualization Performance).
 *
 * All functions are pure, deterministic, and never mutate their input. They
 * exist to bound the DOM / path complexity of charts when a dataset is far
 * larger than any screen can resolve, while keeping the result scientifically
 * meaningful:
 *
 * - `decimateItems` keeps an evenly-spaced stride sample (first and last
 *   elements always preserved) so the distribution shape survives.
 * - `coverageColumns` aggregates per-bin read depth into at most `maxColumns`
 *   pixel columns using the **max** coverage within each column. Max-based
 *   (peak-preserving) binning is the standard for read-depth tracks (e.g.
 *   IGV-style coverage) because averaging would hide genuine signal peaks.
 * - `aggregateHeatmap` block-averages an oversized expression matrix into at
 *   most `maxRows` × `maxCols` blocks so each rendered cell still represents
 *   a real measurement (the mean of its block).
 *
 * Every helper is a no-op (returns equivalent output) when the input already
 * fits inside the requested limit, so small/typical datasets render at full
 * resolution and existing behavior is unchanged.
 *
 * See `docs/visualization/performance.md` for the downsampling strategy and
 * its limitations.
 */

import type { CoverageBin, HeatmapDataset } from './advancedTypes'

/**
 * Returns a deterministic, evenly-spaced sample of at most `maxCount` items.
 *
 * When the input already fits, the items are returned unchanged (same array
 * reference). Otherwise one slot is reserved for the final element and the
 * remaining budget is sampled evenly across the array, so the result is never
 * longer than `maxCount`, always includes the first and last elements (for
 * `maxCount >= 2`), and is fully deterministic for a given input.
 */
export function decimateItems<T>(items: readonly T[], maxCount: number): readonly T[] {
  if (maxCount <= 0) return []
  if (items.length <= maxCount) return items
  if (maxCount === 1) return [items[0]]
  const budget = maxCount - 1
  const stride = Math.ceil((items.length - 1) / budget)
  const sampled: T[] = []
  for (let index = 0; index < items.length - 1; index += stride) {
    sampled.push(items[index])
  }
  sampled.push(items[items.length - 1])
  return sampled
}

/**
 * A coverage measurement after pixel-column aggregation: the representative
 * interval of the column and its peak (max) coverage.
 */
export interface CoverageColumn {
  chromosome: string
  /** 1-based inclusive start of the first bin merged into the column. */
  start: number
  /** 1-based inclusive end of the last bin merged into the column. */
  end: number
  /** Max coverage across the merged bins (peak-preserving). */
  coverage: number
}

/**
 * Aggregates coverage bins into at most `maxColumns` pixel columns using the
 * peak (max) coverage per column. Bins are bucketed by their x-pixel position
 * (`toX(base)` maps a base position to a pixel; the plot is `plotWidth` pixels
 * wide). When the bin count already fits, the input bins are returned unchanged
 * (same array reference). Deterministic for a given input.
 */
export function coverageColumns(
  bins: readonly CoverageBin[],
  toX: (base: number) => number,
  plotWidth: number,
  maxColumns: number,
): readonly CoverageBin[] {
  if (bins.length === 0) return bins
  if (bins.length <= maxColumns || maxColumns <= 0 || plotWidth <= 0) return bins

  const columns: CoverageColumn[] = []
  const columnIndex = new Map<number, CoverageColumn>()
  for (const bin of bins) {
    const pixel = toX(bin.start)
    const raw = Math.floor((pixel / plotWidth) * maxColumns)
    const bucket = Math.min(maxColumns - 1, Math.max(0, raw))
    let column = columnIndex.get(bucket)
    if (column === undefined) {
      column = {
        chromosome: bin.chromosome,
        start: bin.start,
        end: bin.end,
        coverage: bin.coverage,
      }
      columnIndex.set(bucket, column)
      columns.push(column)
    } else {
      if (bin.start < column.start) column.start = bin.start
      if (bin.end > column.end) column.end = bin.end
      if (bin.coverage > column.coverage) column.coverage = bin.coverage
    }
  }
  columns.sort((left, right) => left.start - right.start)
  return columns
}

/** Shape of the block-summarized heatmap produced by `aggregateHeatmap`. */
export interface AggregatedHeatmap {
  rows: string[]
  columns: string[]
  values: Array<Array<number | undefined>>
}

/**
 * Block-averages a heatmap into at most `maxRows` × `maxCols` blocks.
 *
 * Each output cell is the mean of the finite values in its block; blocks with
 * no finite value stay `undefined` (missing). Row/column identifiers are the
 * first identifier of each block, so labels resolve through the original
 * dataset. When the matrix already fits, the dataset is returned unchanged
 * (same reference).
 */
export function aggregateHeatmap(
  dataset: HeatmapDataset,
  maxRows: number,
  maxCols: number,
): HeatmapDataset {
  const rows = dataset.rows
  const columns = dataset.columns
  if (rows.length <= maxRows && columns.length <= maxCols) return dataset

  const safeRows = Math.max(1, maxRows)
  const safeCols = Math.max(1, maxCols)
  const rowBlock = Math.max(1, Math.ceil(rows.length / safeRows))
  const colBlock = Math.max(1, Math.ceil(columns.length / safeCols))

  const aggregatedRows: string[] = []
  const aggregatedCols: string[] = []
  const values: Array<Array<number | undefined>> = []

  for (let r = 0; r < rows.length; r += rowBlock) {
    aggregatedRows.push(rows[r])
  }
  for (let c = 0; c < columns.length; c += colBlock) {
    aggregatedCols.push(columns[c])
  }

  for (let r = 0; r < rows.length; r += rowBlock) {
    const rowOut: Array<number | undefined> = []
    for (let c = 0; c < columns.length; c += colBlock) {
      let sum = 0
      let count = 0
      for (let br = r; br < Math.min(r + rowBlock, rows.length); br += 1) {
        const sourceRow = dataset.values[br]
        if (sourceRow === undefined) continue
        for (let bc = c; bc < Math.min(c + colBlock, columns.length); bc += 1) {
          const value = sourceRow[bc]
          if (value === undefined || !Number.isFinite(value)) continue
          sum += value
          count += 1
        }
      }
      rowOut.push(count > 0 ? sum / count : undefined)
    }
    values.push(rowOut)
  }

  return {
    id: dataset.id,
    title: dataset.title,
    rows: aggregatedRows,
    columns: aggregatedCols,
    values,
    ...(dataset.rowLabels !== undefined ? { rowLabels: { ...dataset.rowLabels } } : {}),
    ...(dataset.columnLabels !== undefined ? { columnLabels: { ...dataset.columnLabels } } : {}),
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}
