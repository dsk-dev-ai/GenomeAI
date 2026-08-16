/**
 * Heatmap validation, normalization, scaling, and tooltips (Phase 6.8).
 *
 * Pure functions over `HeatmapDataset`:
 *
 * - `validateHeatmapDataset` reports structural problems (ragged matrix,
 *   non-finite values, duplicate axis ids) so callers can explain bad data.
 * - `normalizeHeatmapDataset` builds a deterministic, render-ready matrix
 *   (rows/columns ordered canonically, values re-sorted to match, infinite
 *   values dropped, duplicate axis ids deduped).
 * - `heatmapValueDomain` and `heatmapColorScale` drive the color encoding.
 * - `heatmapCellTooltip` maps a cell to the labelled tooltip rows.
 *
 * All functions are pure, locale-independent, and never mutate their input.
 */

import type { HeatmapDataset } from './advancedTypes'
import { type PointTooltip, formatTooltipValue } from './tooltip'
import type { ScientificMetadata } from './types'

export interface HeatmapValidationResult {
  valid: boolean
  errors: string[]
}

function isValidIdentifier(value: string): boolean {
  return value.trim().length > 0
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

/**
 * Reports structural problems with a heatmap. A dataset is valid when every
 * axis id is a non-empty string, row and column ids are unique, the value
 * matrix has one row per row id and one entry per column id per row, and
 * every value is either `undefined` or a finite number.
 */
export function validateHeatmapDataset(dataset: HeatmapDataset): HeatmapValidationResult {
  const errors: string[] = []
  if (!isValidIdentifier(dataset.id)) {
    errors.push('Dataset id must be a non-empty string.')
  }
  if (!isValidIdentifier(dataset.title)) {
    errors.push('Dataset title must be a non-empty string.')
  }
  if (dataset.rows.length !== dataset.values.length) {
    errors.push(
      `Rows (${dataset.rows.length}) do not match the value matrix height (${dataset.values.length}).`,
    )
  }
  const seenRows = new Set<string>()
  dataset.rows.forEach((row, index) => {
    if (!isValidIdentifier(row)) {
      errors.push(`Row ${index}: identifier must be a non-empty string.`)
    } else if (seenRows.has(row)) {
      errors.push(`Duplicate row identifier "${row}".`)
    } else {
      seenRows.add(row)
    }
  })
  const seenColumns = new Set<string>()
  dataset.columns.forEach((column, index) => {
    if (!isValidIdentifier(column)) {
      errors.push(`Column ${index}: identifier must be a non-empty string.`)
    } else if (seenColumns.has(column)) {
      errors.push(`Duplicate column identifier "${column}".`)
    } else {
      seenColumns.add(column)
    }
  })
  dataset.values.forEach((row, rowIndex) => {
    if (row.length !== dataset.columns.length) {
      errors.push(
        `Row ${rowIndex} has ${row.length} values but the dataset declares ${dataset.columns.length} columns.`,
      )
    }
    row.forEach((value, columnIndex) => {
      if (value !== undefined && !Number.isFinite(value)) {
        errors.push(
          `Row ${rowIndex}, column ${columnIndex}: value must be a finite number or undefined.`,
        )
      }
    })
  })
  return { valid: errors.length === 0, errors }
}

/**
 * Builds a deterministic, render-ready heatmap.
 *
 * - Rows and columns are sorted canonically (code-unit order) and the value
 *   matrix is re-arranged to match.
 * - Duplicate axis ids are deduped (first wins) after sorting.
 * - Non-finite values become `undefined` (missing) rather than being dropped,
 *   keeping the matrix rectangular.
 *
 * The returned dataset never shares mutable state with the input.
 */
export function normalizeHeatmapDataset(dataset: HeatmapDataset): HeatmapDataset {
  const rows = uniqueSorted(dataset.rows)
  const columns = uniqueSorted(dataset.columns)

  const values = rows.map((row) => {
    const originalRowIndex = dataset.rows.indexOf(row)
    const rawRow = originalRowIndex >= 0 ? dataset.values[originalRowIndex] : undefined
    return columns.map((column) => {
      if (rawRow === undefined) return undefined
      const originalColumnIndex = dataset.columns.indexOf(column)
      if (originalColumnIndex < 0 || originalColumnIndex >= rawRow.length) return undefined
      const value = rawRow[originalColumnIndex]
      if (value === undefined) return undefined
      return Number.isFinite(value) ? value : undefined
    })
  })

  return {
    id: dataset.id.trim().length > 0 ? dataset.id : 'unnamed-heatmap',
    title: dataset.title.trim().length > 0 ? dataset.title : 'Unnamed heatmap',
    rows,
    columns,
    values,
    ...(dataset.rowLabels !== undefined ? { rowLabels: { ...dataset.rowLabels } } : {}),
    ...(dataset.columnLabels !== undefined ? { columnLabels: { ...dataset.columnLabels } } : {}),
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}

function uniqueSorted(ids: string[]): string[] {
  const seen = new Set<string>()
  const unique = ids
    .filter((id) => isValidIdentifier(id))
    .filter((id) => {
      if (seen.has(id)) return false
      seen.add(id)
      return true
    })
  return unique.sort(compareText)
}

export interface ValueDomain {
  min: number
  max: number
}

/** Whether the matrix holds at least one finite value. */
export function hasRenderableValues(dataset: HeatmapDataset): boolean {
  return dataset.values.some((row) => row.some((value) => value !== undefined))
}

/**
 * The min/max over all finite values in the matrix. Returns `undefined`
 * when the dataset has no finite values.
 */
export function heatmapValueDomain(dataset: HeatmapDataset): ValueDomain | undefined {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  let found = false
  for (const row of dataset.values) {
    for (const value of row) {
      if (value === undefined) continue
      if (value < min) min = value
      if (value > max) max = value
      found = true
    }
  }
  return found ? { min, max } : undefined
}

/** Display name of a row, falling back to the raw identifier. */
export function heatmapRowLabel(dataset: HeatmapDataset, row: string): string {
  const label = dataset.rowLabels?.[row]
  return label !== undefined && label.trim().length > 0 ? label : row
}

/** Display name of a column, falling back to the raw identifier. */
export function heatmapColumnLabel(dataset: HeatmapDataset, column: string): string {
  const label = dataset.columnLabels?.[column]
  return label !== undefined && label.trim().length > 0 ? label : column
}

/**
 * Maps a matrix value to a color.
 *
 * `scale(value)` returns a CSS color string. The scale is diverging around a
 * `center` (default `0`): `domain.min` maps to the low color, `center` maps
 * to the neutral midpoint, and `domain.max` maps to the high color, so
 * negative and positive deviations from the center read as opposites. Missing
 * cells are not colorable — the component renders them separately.
 */
export function heatmapColorScale(
  domain: ValueDomain,
  options: { center?: number; low?: string; mid?: string; high?: string } = {},
): (value: number) => string {
  const center = options.center ?? 0
  const low = options.low ?? '#1d4ed8'
  const mid = options.mid ?? '#f8fafc'
  const high = options.high ?? '#b91c1c'

  const centerPosition = Math.min(1, Math.max(0, (center - domain.min) / (domain.max - domain.min)))

  return (value) => {
    const clamped = Math.min(domain.max, Math.max(domain.min, value))
    const position = (clamped - domain.min) / (domain.max - domain.min)
    if (position <= centerPosition) {
      const t = centerPosition > 0 ? position / centerPosition : 0
      return interpolateColor(low, mid, Math.max(0, Math.min(1, t)))
    }
    const t = centerPosition < 1 ? (position - centerPosition) / (1 - centerPosition) : 1
    return interpolateColor(mid, high, Math.max(0, Math.min(1, t)))
  }
}

function interpolateColor(from: string, to: string, t: number): string {
  const a = hexToRgb(from)
  const b = hexToRgb(to)
  const blend = (channelA: number, channelB: number) =>
    Math.round(channelA + (channelB - channelA) * t)
  return `rgb(${blend(a[0], b[0])}, ${blend(a[1], b[1])}, ${blend(a[2], b[2])})`
}

function hexToRgb(hex: string): [number, number, number] {
  const normalized = hex.replace('#', '')
  const value =
    normalized.length === 3
      ? normalized
          .split('')
          .map((character) => character + character)
          .join('')
      : normalized
  const parsed = Number.parseInt(value, 16)
  if (Number.isNaN(parsed)) return [0, 0, 0]
  return [(parsed >> 16) & 255, (parsed >> 8) & 255, parsed & 255]
}

export interface HeatmapCellCoordinates {
  row: string
  column: string
}

/** Canonical, collision-free key for a heatmap cell (`row` + `column`). */
export function heatmapCellKey(coordinates: HeatmapCellCoordinates): string {
  const { row, column } = coordinates
  return `${row.length}:${row}${column.length}:${column}`
}

/** Parses a key produced by `heatmapCellKey` back into coordinates. */
export function parseHeatmapCellKey(value: string): HeatmapCellCoordinates | undefined {
  const separator = value.indexOf(':')
  if (separator === -1) return undefined
  const lengthText = value.slice(0, separator)
  const length = Number(lengthText)
  if (!Number.isInteger(length) || length < 0) return undefined
  const row = value.slice(separator + 1, separator + 1 + length)
  const rest = value.slice(separator + 1 + length)
  const columnSeparator = rest.indexOf(':')
  if (columnSeparator === -1) return undefined
  const columnLength = Number(rest.slice(0, columnSeparator))
  if (!Number.isInteger(columnLength) || columnLength < 0) return undefined
  const column = rest.slice(columnSeparator + 1, columnSeparator + 1 + columnLength)
  if (separator + 1 + length + columnSeparator + 1 + columnLength !== value.length) {
    return undefined
  }
  return { row, column }
}

/** Metadata of a specific cell (row/column labels or nothing). */
function cellMetadata(
  dataset: HeatmapDataset,
  row: string,
  column: string,
): Record<string, string> | undefined {
  const entries: Record<string, string> = {}
  if (dataset.rowLabels !== undefined && dataset.rowLabels[row] !== undefined) {
    entries.row = dataset.rowLabels[row]
  }
  if (dataset.columnLabels !== undefined && dataset.columnLabels[column] !== undefined) {
    entries.column = dataset.columnLabels[column]
  }
  return Object.keys(entries).length > 0 ? entries : undefined
}

/**
 * Builds the tooltip content for a heatmap cell. The title is the row label,
 * the subtitle the column label, and the rows carry the value plus any axis
 * display labels.
 */
export function heatmapCellTooltip(
  dataset: HeatmapDataset,
  row: string,
  column: string,
  value: number | undefined,
): PointTooltip {
  const rows = []
  if (value === undefined) {
    rows.push({ label: 'Value', value: 'missing' })
  } else {
    rows.push({ label: 'Value', value: formatTooltipValue(value) })
  }
  const meta = cellMetadata(dataset, row, column)
  if (meta !== undefined) {
    for (const [key, entry] of Object.entries(meta)) {
      rows.push({ label: key, value: entry })
    }
  }
  return {
    title: heatmapRowLabel(dataset, row),
    subtitle: heatmapColumnLabel(dataset, column),
    rows,
  }
}
