/**
 * Native chart scales and tick generation (Phase 6.7).
 *
 * Provides the two scale families scientific charts need, implemented
 * natively (no D3 dependency) so the repo keeps its zero-runtime-dependency
 * convention:
 *
 * - `createContinuousScale`: linear mapping of a numeric domain onto a pixel
 *   range (used for the y-axis value scale and for computing tick positions).
 * - `createCategoryScale`: evenly spaced band/point scale over category names
 *   (used for the x-axis samples), including the per-slot step needed to
 *   place series points.
 *
 * Tick generation (`niceTicks`) produces deterministic, human-friendly tick
 * values at 1/2/5 × 10^n steps, unlike `lib/genome/geometry.ts`'s
 * integer-oriented `niceTickStep` which targets base-pair coordinates.
 *
 * All functions are pure, allocation-free of shared mutable state, and locale
 * independent so chart output is deterministic.
 */

/** Linear scale mapping `domain` onto `range` (pixels). */
export interface ContinuousScale {
  domain: [number, number]
  /** Pixel range; `range[0]` maps to `domain[0]`. */
  range: [number, number]
  toPixel: (value: number) => number
  /** Inverse of `toPixel`; returns the domain value at a pixel. */
  invert: (pixel: number) => number
  /** Nicely rounded tick values within the domain, ascending. */
  ticks: (targetCount?: number) => number[]
}

export function createContinuousScale(
  domain: [number, number],
  range: [number, number],
): ContinuousScale {
  const [domainMin, domainMax] = domain
  const [rangeMin, rangeMax] = range
  const domainSpan = domainMax - domainMin
  const rangeSpan = rangeMax - rangeMin

  const toPixel = (value: number): number => {
    if (domainSpan === 0) return rangeMin
    return rangeMin + ((value - domainMin) / domainSpan) * rangeSpan
  }
  const invert = (pixel: number): number => {
    if (rangeSpan === 0) return domainMin
    return domainMin + ((pixel - rangeMin) / rangeSpan) * domainSpan
  }

  return {
    domain,
    range,
    toPixel,
    invert,
    ticks: (targetCount = 5) => niceTicks(domainMin, domainMax, targetCount),
  }
}

export interface TickDefinition {
  value: number
  /** Rendered label; identical to `value` when it stays exact. */
  label: string
}

/**
 * Computes a "nice" tick step at 1/2/5 × 10^n within a max number of steps.
 *
 * Unlike `lib/genome/geometry.ts`'s integer-only `niceTickStep` (which targets
 * whole-base genomic coordinates), this variant supports fractional and
 * negative domains because expression values are arbitrary reals.
 */
export function continuousNiceTickStep(min: number, max: number, targetCount = 5): number {
  const count = targetCount < 1 ? 1 : targetCount
  if (!Number.isFinite(min) || !Number.isFinite(max) || max === min) return 1
  const rawStep = (max - min) / Math.max(count, 1)
  if (rawStep <= 0) return 1
  const magnitude = 10 ** Math.floor(Math.log10(rawStep))
  const candidates = [1, 2, 5, 10]
  let step = magnitude
  for (const candidate of candidates) {
    const candidateStep = candidate * magnitude
    if (candidateStep >= rawStep) {
      step = candidateStep
      break
    }
    step = candidateStep
  }
  return step
}

/**
 * Deterministic, ascending tick values for a domain, snapped to a nice step.
 * Supports negative and fractional domains.
 */
export function niceTicks(min: number, max: number, targetCount = 5): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return []
  if (max < min) return []
  if (max === min) return [min]
  const step = continuousNiceTickStep(min, max, targetCount)
  const first = Math.ceil(min / step) * step
  const ticks: number[] = []
  const decimals = Math.max(0, -Math.floor(Math.log10(step)))
  for (let value = first; value <= max + step / 1e9; value += step) {
    ticks.push(Number(value.toFixed(decimals)))
    if (ticks.length > 100) break
  }
  return ticks
}

/**
 * Renders a numeric value for axis labels: trims trailing zeros from
 * floating-point artifacts and uses a compact suffix for very large values.
 */
export function formatTickValue(value: number): string {
  if (!Number.isFinite(value)) return ''
  const magnitude = Math.abs(value)
  if (magnitude >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (magnitude >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return Number(value.toFixed(6)).toString()
}

/** Equal-width slots for ordered category names over a pixel range. */
export interface CategoryScale {
  domain: readonly string[]
  range: [number, number]
  /** Distance between slot centers. */
  step: number
  /** Horizontal padding (in pixels) reserved at each end of the range. */
  padding: number
  /** Pixel center of a category slot; `undefined` for unknown categories. */
  toPixel: (category: string) => number
  /** Index of a category within `domain`, or `-1`. */
  indexOf: (category: string) => number
  /** The pixel extent (x0, x1) of a slot; `undefined` for unknown categories. */
  slot: (category: string) => [number, number] | undefined
}

export function createCategoryScale(
  categories: readonly string[],
  range: [number, number],
  padding = 0.2,
): CategoryScale {
  const [rangeMin, rangeMax] = range
  const rangeSpan = rangeMax - rangeMin
  const count = categories.length
  const step = count > 1 ? rangeSpan / (count - 1) : 0
  const indexMap = new Map(categories.map((category, index) => [category, index]))

  const toPixel = (category: string): number => {
    const index = indexMap.get(category)
    if (index === undefined) return rangeMin
    if (count === 1) return rangeMin + rangeSpan / 2
    return rangeMin + (index / (count - 1)) * rangeSpan
  }

  return {
    domain: categories,
    range,
    step,
    padding,
    toPixel,
    indexOf: (category: string): number => {
      const index = indexMap.get(category)
      return index === undefined ? -1 : index
    },
    slot: (category: string): [number, number] | undefined => {
      const index = indexMap.get(category)
      if (index === undefined) return undefined
      if (count === 1) return [rangeMin, rangeMax]
      const half = rangeSpan / (2 * (count - 1))
      return [toPixel(category) - half, toPixel(category) + half]
    },
  }
}

/**
 * Selects which category labels fit along the x-axis without overlap.
 *
 * Returns `{ samples, visible }` where every entry carries its center pixel
 * and a `visible` flag. Labels that do not fit are hidden (rather than
 * rotated or dropped) so the axis stays readable and deterministic for any
 * number of samples.
 */
export function categoryLabelTicks(
  scale: CategoryScale,
  plotWidth: number,
  minLabelGap = 36,
): Array<{ sample: string; x: number; visible: boolean }> {
  const count = scale.domain.length
  if (count === 0) return []
  const step = plotWidth / Math.max(count, 1)
  const everyNth = Math.max(1, Math.ceil(minLabelGap / Math.max(step, 1)))
  return scale.domain.map((sample, index) => ({
    sample,
    x: scale.toPixel(sample),
    visible: index % everyNth === 0,
  }))
}
