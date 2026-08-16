/**
 * Volcano plot validation, normalization, thresholds, and tooltips (Phase 6.8).
 *
 * Pure functions over `VolcanoDataset`:
 *
 * - `validateVolcanoDataset` reports invalid points (empty identifiers,
 *   non-finite effect sizes/significance).
 * - `normalizeVolcanoDataset` builds a deterministic, render-ready dataset
 *   (invalid points dropped, duplicate identifiers deduped, points ordered
 *   canonically).
 * - `volcanoDomains` derives the x/y value domains used by the scales.
 * - `isVolcanoHighlighted` marks points that pass user-supplied thresholds.
 * - `volcanoPointTooltip` maps a point to the labelled tooltip rows.
 *
 * All functions are pure, locale-independent, and never mutate their input.
 */

import type { VolcanoDataset, VolcanoPoint } from './advancedTypes'
import { type PointTooltip, formatTooltipValue } from './tooltip'

export interface VolcanoValidationResult {
  valid: boolean
  errors: string[]
}

function isValidIdentifier(value: string): boolean {
  return value.trim().length > 0
}

/** Reports problems with a volcano dataset. Empty identifiers or non-finite
 * numeric fields are invalid. */
export function validateVolcanoDataset(dataset: VolcanoDataset): VolcanoValidationResult {
  const errors: string[] = []
  if (!isValidIdentifier(dataset.id)) {
    errors.push('Dataset id must be a non-empty string.')
  }
  if (!isValidIdentifier(dataset.title)) {
    errors.push('Dataset title must be a non-empty string.')
  }
  dataset.points.forEach((point, index) => {
    if (!isValidIdentifier(point.identifier)) {
      errors.push(`Point ${index}: identifier must be a non-empty string.`)
    }
    if (!Number.isFinite(point.effectSize)) {
      errors.push(`Point ${index}: effectSize must be a finite number.`)
    }
    if (!Number.isFinite(point.significance)) {
      errors.push(`Point ${index}: significance must be a finite number.`)
    }
    if (point.adjustedSignificance !== undefined && !Number.isFinite(point.adjustedSignificance)) {
      errors.push(`Point ${index}: adjustedSignificance must be a finite number.`)
    }
  })
  return { valid: errors.length === 0, errors }
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

/**
 * Builds a deterministic, render-ready volcano dataset: invalid points are
 * dropped, duplicate identifiers are deduped (first wins), and points are
 * ordered canonically by identifier. The result is always structurally valid
 * and never shares mutable state with the input.
 */
export function normalizeVolcanoDataset(dataset: VolcanoDataset): VolcanoDataset {
  const seen = new Set<string>()
  const points = dataset.points
    .filter((point) => {
      if (!isValidIdentifier(point.identifier)) return false
      if (!Number.isFinite(point.effectSize)) return false
      if (!Number.isFinite(point.significance)) return false
      if (
        point.adjustedSignificance !== undefined &&
        !Number.isFinite(point.adjustedSignificance)
      ) {
        return false
      }
      if (seen.has(point.identifier)) return false
      seen.add(point.identifier)
      return true
    })
    .map(clonePoint)
    .sort((left, right) => compareText(left.identifier, right.identifier))

  return {
    id: dataset.id.trim().length > 0 ? dataset.id : 'unnamed-volcano',
    title: dataset.title.trim().length > 0 ? dataset.title : 'Unnamed volcano plot',
    points,
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}

function clonePoint(point: VolcanoPoint): VolcanoPoint {
  return {
    ...point,
    ...(point.adjustedSignificance !== undefined
      ? { adjustedSignificance: point.adjustedSignificance }
      : {}),
    ...(point.metadata !== undefined ? { metadata: { ...point.metadata } } : {}),
  }
}

export interface ValueDomain {
  min: number
  max: number
}

/** Whether the dataset holds at least one renderable point. */
export function hasRenderablePoints(dataset: VolcanoDataset): boolean {
  return dataset.points.length > 0
}

export interface VolcanoDomains {
  effectSize: ValueDomain
  significance: ValueDomain
}

/**
 * The x/y domains for a volcano plot. The effect-size domain is symmetric
 * around zero (the natural null point for a fold change) when the data spans
 * both signs; the significance domain always starts at zero. Returns
 * `undefined` for an empty dataset.
 */
export function volcanoDomains(dataset: VolcanoDataset): VolcanoDomains | undefined {
  if (dataset.points.length === 0) return undefined
  let minEffect = Number.POSITIVE_INFINITY
  let maxEffect = Number.NEGATIVE_INFINITY
  let maxSignificance = Number.NEGATIVE_INFINITY
  for (const point of dataset.points) {
    if (point.effectSize < minEffect) minEffect = point.effectSize
    if (point.effectSize > maxEffect) maxEffect = point.effectSize
    if (point.significance > maxSignificance) maxSignificance = point.significance
  }
  const effectSize = { min: minEffect, max: maxEffect }
  if (effectSize.min > 0 || effectSize.max < 0) {
    // Symmetrize so zero is always centered when data is single-signed.
    const magnitude = Math.max(Math.abs(effectSize.min), Math.abs(effectSize.max))
    effectSize.min = -magnitude
    effectSize.max = magnitude
  }
  return { effectSize, significance: { min: 0, max: maxSignificance } }
}

/**
 * Whether a point passes the user-supplied significance callout thresholds.
 * The callout is a visual aid only — the chart never infers statistical
 * significance on its own.
 */
export function isVolcanoHighlighted(
  point: VolcanoPoint,
  options: { effectThreshold?: number; significanceThreshold?: number } = {},
): boolean {
  const { effectThreshold = 0, significanceThreshold = 0 } = options
  const aboveEffect = Math.abs(point.effectSize) >= effectThreshold
  const aboveSignificance = point.significance >= significanceThreshold
  return aboveEffect && aboveSignificance
}

/**
 * Builds the tooltip content for a volcano point. The title is the feature
 * identifier, the subtitle describes its position, and the rows carry the
 * effect size, significance, optional adjusted significance, and any
 * metadata fields.
 */
export function volcanoPointTooltip(point: VolcanoPoint): PointTooltip {
  const rows = [
    { label: 'Effect size', value: formatTooltipValue(point.effectSize) },
    { label: 'Significance', value: formatTooltipValue(point.significance) },
  ]
  if (point.adjustedSignificance !== undefined) {
    rows.push({
      label: 'Adjusted significance',
      value: formatTooltipValue(point.adjustedSignificance),
    })
  }
  if (point.metadata !== undefined) {
    for (const [key, value] of Object.entries(point.metadata)) {
      rows.push({ label: key, value: String(value) })
    }
  }
  return { title: point.identifier, subtitle: 'Differential expression result', rows }
}
