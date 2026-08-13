/**
 * Scientific chart data model (Phase 6.7).
 *
 * The dataset types describe quantitative measurements (starting with gene
 * expression) grouped into series of points. The types are intentionally
 * generic about measurement *kind*: any numeric measurement with a stable
 * per-point identifier and a categorical grouping dimension maps onto them,
 * so the same chart infrastructure can serve later scientific charts
 * (coverage, statistical comparisons, QC metrics, ...) without rework.
 *
 * The chart infrastructure itself (`lib/scientific/scale.ts`,
 * `lib/scientific/geometry.ts`) is measurement-agnostic — it only consumes
 * numbers, categories, and labels.
 */

/** Free-form metadata attached to a point, series, or dataset. */
export type ScientificMetadata = Record<string, string | number | boolean>

/**
 * A single quantitative measurement.
 *
 * `identifier` is the stable per-dataset id of the measured entity (e.g. a
 * gene) within its series, `sample` is the categorical grouping shown on the
 * chart's x-axis, and `value` is the measurement shown on the y-axis.
 * `normalizedValue`, when present, is an alternative representation (e.g.
 * z-score / log-transformed) rendered when the user switches views.
 */
export interface ExpressionPoint {
  identifier: string
  sample: string
  value: number
  normalizedValue?: number
  metadata?: ScientificMetadata
}

/**
 * A named group of points sharing the same measured entity (e.g. one gene
 * measured across several samples). Series id must be unique within a
 * dataset.
 */
export interface ExpressionSeries {
  id: string
  label: string
  points: ExpressionPoint[]
}

/**
 * A full scientific dataset: a titled collection of series.
 *
 * The dataset carries only measurement data plus optional metadata; all
 * rendering concerns (scales, axes, tooltips, selection) are derived by the
 * pure modules under `lib/scientific` and composed by the view-model hook
 * `useExpressionChart`.
 */
export interface ExpressionDataset {
  id: string
  title: string
  series: ExpressionSeries[]
  metadata?: ScientificMetadata
}

/**
 * Stable identity of a single point within a dataset: the series id, the
 * measured entity identifier (e.g. a gene), and the sample. Series + entity +
 * sample is the unique triple for one measurement, so interactions (selection,
 * keyboard navigation, tooltips) survive re-renders and re-ordering.
 */
export interface PointKey {
  seriesId: string
  pointId: string
  sample: string
}

/** Renders a canonical, collision-free key for a `PointKey`. */
export function pointKeyToString(key: PointKey): string {
  return `${key.seriesId}:${key.pointId}@${key.sample}`
}

/** Parses a string produced by `pointKeyToString` back into a `PointKey`. */
export function parsePointKey(value: string): PointKey | undefined {
  const atIndex = value.indexOf('@')
  if (atIndex === -1) return undefined
  const seriesPart = value.slice(0, atIndex)
  const sample = value.slice(atIndex + 1)
  const separatorIndex = seriesPart.indexOf(':')
  if (separatorIndex === -1) return undefined
  return {
    seriesId: seriesPart.slice(0, separatorIndex),
    pointId: seriesPart.slice(separatorIndex + 1),
    sample,
  }
}
