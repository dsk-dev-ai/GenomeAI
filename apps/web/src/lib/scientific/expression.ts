/**
 * Expression dataset validation and normalization (Phase 6.7).
 *
 * Pure functions over `ExpressionDataset`:
 *
 * - `validateExpressionDataset` reports invalid points/series so callers can
 *   explain bad data instead of silently dropping it.
 * - `normalizeExpressionDataset` builds a deterministic, render-ready dataset
 *   (invalid points dropped, duplicate identifiers deduped, series and points
 *   ordered canonically).
 * - `availableSamples`, `expressionDomain`, and `hasRenderablePoints` derive
 *   the x-axis categories, y-axis value domain, and emptiness used by the
 *   chart layout.
 *
 * Normalization is deliberately idempotent and locale-independent so chart
 * output is deterministic across runs and environments.
 */

import type {
  ExpressionDataset,
  ExpressionPoint,
  ExpressionSeries,
  ScientificMetadata,
} from './types'

/** Value fields that can drive the y-axis. */
export type ExpressionValueField = 'value' | 'normalizedValue'

export interface ExpressionValidationResult {
  valid: boolean
  errors: string[]
}

function isValidIdentifier(value: string): boolean {
  return value.trim().length > 0
}

function isFiniteMeasurement(value: number): boolean {
  return Number.isFinite(value)
}

/** Reports problems with a single point. Returns an empty array when valid. */
export function validateExpressionPoint(
  point: ExpressionPoint,
  index: number,
  seriesId: string,
): string[] {
  const errors: string[] = []
  if (!isValidIdentifier(point.identifier)) {
    errors.push(`Series ${seriesId} point ${index}: identifier must be a non-empty string.`)
  }
  if (!isValidIdentifier(point.sample)) {
    errors.push(`Series ${seriesId} point ${index}: sample must be a non-empty string.`)
  }
  if (!isFiniteMeasurement(point.value)) {
    errors.push(`Series ${seriesId} point ${index}: value must be a finite number.`)
  }
  if (point.normalizedValue !== undefined && !isFiniteMeasurement(point.normalizedValue)) {
    errors.push(`Series ${seriesId} point ${index}: normalizedValue must be a finite number.`)
  }
  return errors
}

/** Reports problems with a series. Returns an empty array when valid. */
export function validateExpressionSeries(series: ExpressionSeries, index: number): string[] {
  const errors: string[] = []
  if (!isValidIdentifier(series.id)) {
    errors.push(`Series ${index}: id must be a non-empty string.`)
  }
  if (!isValidIdentifier(series.label)) {
    errors.push(`Series ${index}: label must be a non-empty string.`)
  }
  return errors
}

/**
 * Validates a complete dataset, returning every problem found. A dataset is
 * valid when every series has an id and label and every point has an
 * identifier, a sample, and a finite value.
 */
export function validateExpressionDataset(dataset: ExpressionDataset): ExpressionValidationResult {
  const errors: string[] = []
  if (!isValidIdentifier(dataset.id)) {
    errors.push('Dataset id must be a non-empty string.')
  }
  if (!isValidIdentifier(dataset.title)) {
    errors.push('Dataset title must be a non-empty string.')
  }
  dataset.series.forEach((series, seriesIndex) => {
    errors.push(...validateExpressionSeries(series, seriesIndex))
    series.points.forEach((point, pointIndex) => {
      errors.push(...validateExpressionPoint(point, pointIndex, series.id))
    })
  })
  const seriesIds = dataset.series.map((series) => series.id)
  const duplicateSeriesIds = seriesIds.filter((id, index) => seriesIds.indexOf(id) !== index)
  for (const duplicateId of [...new Set(duplicateSeriesIds)]) {
    errors.push(`Duplicate series id "${duplicateId}".`)
  }
  return { valid: errors.length === 0, errors }
}

function asFiniteNumber(value: number): boolean {
  return Number.isFinite(value)
}

/**
 * Dedupes points within a series, keeping the first occurrence of each
 * (identifier, sample) pair — one measurement per entity per sample. Stable
 * and deterministic.
 */
export function dedupePoints(points: ExpressionPoint[]): ExpressionPoint[] {
  const seen = new Set<string>()
  const result: ExpressionPoint[] = []
  for (const point of points) {
    if (point.identifier.trim().length === 0) continue
    if (point.sample.trim().length === 0) continue
    const key = `${point.identifier}\u0000${point.sample}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push(point)
  }
  return result
}

/**
 * Builds a deterministic, render-ready dataset from raw input.
 *
 * - Series and points are sorted canonically (series by id, points by sample
 *   then identifier) so charts render identically across runs.
 * - Invalid points (empty identifier/sample or non-finite value) are dropped.
 * - Duplicate point identifiers within a series are deduped (first wins).
 * - Duplicate series ids are deduped (first wins).
 *
 * The returned dataset is always structurally valid (`validateExpressionDataset`
 * passes) and never shares mutable state with the input.
 */
export function normalizeExpressionDataset(dataset: ExpressionDataset): ExpressionDataset {
  const seenSeriesIds = new Set<string>()
  const series = dataset.series
    .filter((series) => {
      if (!isValidIdentifier(series.id) || !isValidIdentifier(series.label)) return false
      if (seenSeriesIds.has(series.id)) return false
      seenSeriesIds.add(series.id)
      return true
    })
    .map((series) => {
      const points = dedupePoints(series.points)
        .filter((point) => {
          if (!isValidIdentifier(point.identifier)) return false
          if (!isValidIdentifier(point.sample)) return false
          if (!asFiniteNumber(point.value)) return false
          if (point.normalizedValue !== undefined && !asFiniteNumber(point.normalizedValue)) {
            return false
          }
          return true
        })
        .sort(
          (left, right) =>
            compareText(left.sample, right.sample) ||
            compareText(left.identifier, right.identifier),
        )
      return { ...series, points: points.map(clonePoint) }
    })
    .sort((left, right) => compareText(left.id, right.id))

  return {
    id: dataset.id.trim().length > 0 ? dataset.id : 'unnamed-dataset',
    title: dataset.title.trim().length > 0 ? dataset.title : 'Unnamed dataset',
    series,
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}

/**
 * Compares two strings in code-unit order. Unlike `String.prototype.localeCompare`
 * (which depends on the runtime's active locale), this ordering is identical
 * across every environment, keeping normalized output deterministic.
 */
function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

/** Shallow copy of a point (including its metadata) so the input stays untouched. */
function clonePoint(point: ExpressionPoint): ExpressionPoint {
  return {
    ...point,
    ...(point.metadata !== undefined ? { metadata: { ...point.metadata } } : {}),
  }
}

/**
 * The sorted, unique set of sample names across every series. Drives the
 * categorical x-axis; ordering is deterministic (code-unit compare).
 */
export function availableSamples(dataset: ExpressionDataset): string[] {
  const samples = new Set<string>()
  for (const series of dataset.series) {
    for (const point of series.points) {
      if (point.sample.trim().length > 0) samples.add(point.sample)
    }
  }
  return [...samples].sort((left, right) => compareText(left, right))
}

export interface ValueDomain {
  min: number
  max: number
}

/**
 * The min/max of the chosen value field across all points in a series.
 * Returns `undefined` when the series has no usable points for that field.
 */
export function seriesDomain(
  series: ExpressionSeries,
  field: ExpressionValueField,
): ValueDomain | undefined {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  for (const point of series.points) {
    const value = point[field]
    if (value === undefined || !Number.isFinite(value)) continue
    if (value < min) min = value
    if (value > max) max = value
  }
  return Number.isFinite(min) ? { min, max } : undefined
}

/**
 * The min/max of the chosen value field across all series.
 * Returns `undefined` when the dataset has no usable points for that field.
 */
export function datasetDomain(
  dataset: ExpressionDataset,
  field: ExpressionValueField,
): ValueDomain | undefined {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  let found = false
  for (const series of dataset.series) {
    const domain = seriesDomain(series, field)
    if (domain === undefined) continue
    found = true
    if (domain.min < min) min = domain.min
    if (domain.max > max) max = domain.max
  }
  return found ? { min, max } : undefined
}

/** True when the dataset contains at least one finite point. */
export function hasRenderablePoints(dataset: ExpressionDataset): boolean {
  return dataset.series.some((series) =>
    series.points.some((point) => Number.isFinite(point.value) && point.sample.trim().length > 0),
  )
}

/** True when any point in the dataset carries a normalized value. */
export function hasNormalizedValues(dataset: ExpressionDataset): boolean {
  return dataset.series.some((series) =>
    series.points.some((point) => point.normalizedValue !== undefined),
  )
}

/**
 * The y-axis domain for a value field with a scientifically sensible
 * default: all-non-negative measurements start at zero, all-negative
 * measurements end at zero, and degenerate single-value datasets are padded.
 * Returns `{ min: 0, max: 1 }` when the dataset has no usable points.
 */
export function expressionValueDomain(
  dataset: ExpressionDataset,
  field: ExpressionValueField,
): ValueDomain {
  const raw = datasetDomain(dataset, field)
  if (raw === undefined) return { min: 0, max: 1 }
  let { min, max } = raw
  if (min >= 0) min = 0
  if (max < 0) max = 0
  if (min === max) {
    const pad = Math.max(1, Math.abs(max) * 0.5)
    return { min: min - pad, max: max + pad }
  }
  return { min, max }
}

/** Copy of a point's metadata with every key/entry coerced to safe scalars. */
export function sanitizeMetadata(metadata: unknown): ScientificMetadata | undefined {
  if (typeof metadata !== 'object' || metadata === null || Array.isArray(metadata)) return undefined
  const entries = Object.entries(metadata).filter(
    (entry): entry is [string, string | number | boolean] => {
      const [, field] = entry
      return typeof field === 'string' || typeof field === 'number' || typeof field === 'boolean'
    },
  )
  return entries.length > 0 ? Object.fromEntries(entries) : undefined
}
