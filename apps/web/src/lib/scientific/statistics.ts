/**
 * Deterministic summary statistics (Phase 6.8).
 *
 * Pure, locale-independent statistics used by the statistical distribution
 * chart and, later, by coverage/QC summaries. Everything here operates on a
 * single numeric sample or a grouped set of values and returns the same
 * result on every run so charts and their tests stay reproducible.
 */

/** Summary statistics for a single numeric sample. */
export interface SummaryStatistics {
  count: number
  mean: number
  min: number
  max: number
  /** First quartile (25th percentile). */
  q1: number
  /** Second quartile / median (50th percentile). */
  q2: number
  /** Third quartile (75th percentile). */
  q3: number
  /** Interquartile range (`q3 - q1`). */
  iqr: number
}

/** Whisker bounds computed from a sample (Tukey box-plot convention). */
export interface Whiskers {
  /** Smallest sample value within `1.5 * IQR` of the first quartile. */
  lower: number
  /** Largest sample value within `1.5 * IQR` of the third quartile. */
  upper: number
  /** Outliers beyond the whiskers, in ascending order. */
  outliers: number[]
}

/**
 * Returns the sample sorted ascending using code-unit order. The input array
 * is not mutated.
 */
export function sortedSample(values: readonly number[]): number[] {
  return [...values].filter((value) => Number.isFinite(value)).sort((left, right) => left - right)
}

/**
 * Linear-interpolation quantile (the `R-7`/Excel convention) for a sorted
 * sample. `q` must be in `[0, 1]`. Returns `NaN` for an empty sample.
 */
export function quantile(sorted: readonly number[], q: number): number {
  if (sorted.length === 0) return Number.NaN
  const clamped = Math.min(1, Math.max(0, q))
  const position = clamped * (sorted.length - 1)
  const lower = Math.floor(position)
  const upper = Math.ceil(position)
  if (lower === upper) return sorted[lower]
  const fraction = position - lower
  return sorted[lower] + (sorted[upper] - sorted[lower]) * fraction
}

/**
 * Summary statistics for a sample of finite values. Returns `undefined` for
 * an empty sample (the caller decides how to present missing data).
 */
export function summarize(values: readonly number[]): SummaryStatistics | undefined {
  const sorted = sortedSample(values)
  if (sorted.length === 0) return undefined
  const q1 = quantile(sorted, 0.25)
  const q2 = quantile(sorted, 0.5)
  const q3 = quantile(sorted, 0.75)
  const iqr = q3 - q1
  let sum = 0
  for (const value of sorted) sum += value
  return {
    count: sorted.length,
    mean: sum / sorted.length,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    q1,
    q2,
    q3,
    iqr,
  }
}

/**
 * Tukey box-plot whiskers: the farthest sample value within `1.5 * IQR` of
 * each quartile, with everything beyond reported as outliers. Returns
 * `undefined` when the sample has no statistics (empty input).
 */
export function boxPlotWhiskers(values: readonly number[]): Whiskers | undefined {
  const summary = summarize(values)
  if (summary === undefined) return undefined
  const lowerLimit = summary.q1 - 1.5 * summary.iqr
  const upperLimit = summary.q3 + 1.5 * summary.iqr
  const sorted = sortedSample(values)
  const outliers: number[] = []
  let lower = summary.min
  let upper = summary.max
  for (const value of sorted) {
    if (value < lowerLimit) {
      outliers.push(value)
    } else {
      lower = value
      break
    }
  }
  for (let index = sorted.length - 1; index >= 0; index -= 1) {
    const value = sorted[index]
    if (value > upperLimit) {
      outliers.push(value)
    } else {
      upper = value
      break
    }
  }
  outliers.sort((left, right) => left - right)
  return { lower, upper, outliers }
}
