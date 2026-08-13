/**
 * Pixel geometry for the Genome Browser (Phase 6.2).
 *
 * Maps one-based inclusive genomic positions to x pixels within the SVG
 * viewport, and computes axis tick positions. Pure functions kept separate
 * from rendering so they can be unit-tested without a DOM.
 */

/** Maps base positions to x coordinates for a given pixel width. */
export interface GenomeScale {
  /** Pixel width of the drawing area. */
  width: number
  /** Pixels per base. */
  pxPerBase: number
  /** Converts a one-based base position to an x pixel. */
  toX: (position: number) => number
  /** Converts a base span (inclusive, `end - start + 1`) to pixels. */
  spanToPixels: (bases: number) => number
}

/**
 * Builds a scale for a viewport spanning `start..end` (inclusive) drawn
 * into `width` pixels.
 */
export function createScale(start: number, end: number, width: number): GenomeScale {
  const bases = Math.max(1, end - start + 1)
  const pxPerBase = width / bases
  return {
    width,
    pxPerBase,
    toX: (position: number) => (position - start) * pxPerBase,
    spanToPixels: (basesCount: number) => basesCount * pxPerBase,
  }
}

/** A labelled axis tick. */
export interface AxisTick {
  /** Base position of the tick. */
  position: number
  /** Human-readable label, e.g. `124.5M`. */
  label: string
  /** Whether it is a major tick (labelled). */
  major: boolean
}

/** Powers of ten steps that produce "nice" tick spacing. */
const NICE_STEPS = [1, 2, 5, 10]

/**
 * Picks a nice tick step (1/2/5 × 10ⁿ bases) close to `targetStep` while
 * keeping it >= `minStep`.
 */
export function niceTickStep(targetStep: number, minStep: number): number {
  if (!Number.isFinite(targetStep) || targetStep <= 0) return 1
  const order = 10 ** Math.floor(Math.log10(targetStep))
  let step = order
  for (const nice of NICE_STEPS) {
    if (nice * order >= targetStep) {
      step = nice * order
      break
    }
  }
  return Math.max(step, minStep)
}

/**
 * Generates major labelled ticks and unlabelled minor ticks across a
 * one-based inclusive interval.
 *
 * @param start first base (inclusive)
 * @param end last base (inclusive)
 * @param targetTicks approximate number of major ticks wanted
 * @param minorPerMajor number of minor ticks between major ticks (>= 1)
 */
export function computeTicks(
  start: number,
  end: number,
  targetTicks = 10,
  minorPerMajor = 4,
): AxisTick[] {
  const bases = Math.max(1, end - start + 1)
  const targetStep = bases / targetTicks
  const majorStep = niceTickStep(targetStep, 1)
  // Keep every step an integer (>= 1) so tick positions are whole base
  // positions, consistent with the one-based coordinate model.
  const divisions = Math.max(1, Math.floor(minorPerMajor))
  const minorStep = Math.max(1, Math.floor(majorStep / divisions))

  const ticks: AxisTick[] = []
  const firstMajor = Math.ceil(start / majorStep) * majorStep
  const lastMajor = Math.floor(end / majorStep) * majorStep

  // Minor ticks between major ticks, plus leading/trailing partial ones.
  let minorStart = Math.floor(start / minorStep) * minorStep
  let minorEnd = Math.ceil(end / minorStep) * minorStep
  minorStart = Math.max(minorStart, start)
  minorEnd = Math.min(minorEnd, end)
  for (let pos = minorStart; pos <= minorEnd; pos += minorStep) {
    if (pos >= firstMajor && pos <= lastMajor && pos % majorStep === 0) continue
    ticks.push({ position: pos, label: '', major: false })
  }

  for (let pos = firstMajor; pos <= lastMajor; pos += majorStep) {
    ticks.push({ position: pos, label: formatBasePosition(pos), major: true })
  }

  ticks.sort((a, b) => a.position - b.position)
  return ticks
}

/**
 * Formats a base position for axis display, e.g. `1.24M`, `15K`, `230`.
 */
export function formatBasePosition(position: number): string {
  if (position >= 1_000_000) {
    const millions = position / 1_000_000
    return `${trimTrailingZeros(millions.toFixed(3))}M`
  }
  if (position >= 1_000) {
    const thousands = position / 1_000
    return `${trimTrailingZeros(thousands.toFixed(2))}K`
  }
  return String(position)
}

function trimTrailingZeros(value: string): string {
  return value.replace(/\.?0+$/, '')
}

/**
 * Formats a region label used by the browser status, e.g.
 * `chr1:124,500,000-125,000,000`.
 */
export function formatRegionLabel(chromosome: string, start: number, end: number): string {
  return `${chromosome}:${formatGrouped(start)}-${formatGrouped(end)}`
}

function formatGrouped(value: number): string {
  return value.toLocaleString('en-US')
}

/** A horizontal segment with pixel coordinates ready for SVG rendering. */
export interface PixelSpan {
  x: number
  width: number
}

/** Geometry of a rendered feature interval on the canvas. */
export interface RenderedSpan {
  /** Horizontal span in pixel space (may be partially clipped). */
  span: PixelSpan
  /** True when at least part of the span is inside the viewport. */
  visible: boolean
}

/** The structural window shape required by interval clipping. */
export type IntervalWindow = { start: number; end: number }

/**
 * Clips an inclusive interval to a window and converts it to a pixel span.
 * Returns `visible: false` when the interval does not intersect the window
 * at all. Works for any one-based-inclusive interval (genomic base positions,
 * protein residues, ...) so it is shared by every visualization module.
 */
export function intervalToPixels(
  scale: GenomeScale,
  viewport: IntervalWindow,
  start: number,
  end: number,
): RenderedSpan {
  const clipStart = Math.max(start, viewport.start)
  const clipEnd = Math.min(end, viewport.end)
  if (clipStart > clipEnd) return { span: { x: 0, width: 0 }, visible: false }

  const x = scale.toX(clipStart)
  const width = scale.spanToPixels(clipEnd - clipStart + 1)
  return { span: { x, width }, visible: true }
}
