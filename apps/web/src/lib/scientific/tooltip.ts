/**
 * Chart tooltip row mapping (Phase 6.7).
 *
 * Pure function that turns a selected point into the labelled rows shown in
 * the hover tooltip and the accessible detail panel. Kept outside the
 * component so the mapping is unit-testable and identical in both places.
 */

import type { ExpressionDataset, ExpressionPoint, ExpressionSeries, PointKey } from './types'

export interface TooltipRow {
  label: string
  value: string
}

export interface PointTooltip {
  title: string
  subtitle: string
  rows: TooltipRow[]
}

/** Formats a finite number for tooltips, trimming floating-point noise. */
export function formatTooltipValue(value: number): string {
  if (!Number.isFinite(value)) return '–'
  return Number(value.toFixed(4)).toString()
}

/**
 * Builds the tooltip content for a point. The title is the series label, the
 * subtitle identifies the point (identifier / sample), and the rows carry the
 * sample, value, optional normalized value, and any metadata fields.
 */
export function pointTooltip(series: ExpressionSeries, point: ExpressionPoint): PointTooltip {
  const rows: TooltipRow[] = [
    { label: 'Sample', value: point.sample },
    { label: 'Value', value: formatTooltipValue(point.value) },
  ]
  if (point.normalizedValue !== undefined) {
    rows.push({ label: 'Normalized', value: formatTooltipValue(point.normalizedValue) })
  }
  if (point.metadata !== undefined) {
    for (const [key, value] of Object.entries(point.metadata)) {
      rows.push({ label: key, value: String(value) })
    }
  }
  const subtitle = `${point.identifier} — ${point.sample}`
  return { title: series.label, subtitle, rows }
}

export interface LookupResult {
  series: ExpressionSeries
  point: ExpressionPoint
}

/** Finds a point by its `PointKey`. Returns `undefined` when missing. */
export function lookupPoint(dataset: ExpressionDataset, key: PointKey): LookupResult | undefined {
  const series = dataset.series.find((candidate) => candidate.id === key.seriesId)
  if (series === undefined) return undefined
  const point = series.points.find(
    (candidate) => candidate.identifier === key.pointId && candidate.sample === key.sample,
  )
  if (point === undefined) return undefined
  return { series, point }
}
