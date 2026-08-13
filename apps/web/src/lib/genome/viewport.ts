/**
 * Genome viewport navigation — pure functions (Phase 6.2).
 *
 * A viewport is the currently visible window over a chromosome contig. All
 * coordinates are one-based and inclusive (`start..end`, length
 * `end - start + 1` bases; see `lib/genome/types.ts`).
 *
 * Navigation is deliberately stateless: every operation takes an immutable
 * `GenomeViewport` and returns a new one, which keeps the math trivial to
 * test and compose with React state. Clamping is applied whenever the
 * contig size is known (`bounds`); otherwise the high side is open-ended.
 */

import type { GenomeViewport, IntervalWindow } from './types'

/** Minimum viewport width in bases (maximum zoom-in). */
export const MIN_VIEWPORT_BASES = 1

/** Fraction of the current viewport moved per pan action. */
export const PAN_FRACTION = 0.5

/** Factor applied to the viewport size per zoom action. */
export const ZOOM_FACTOR = 1.5

/**
 * Number of one-based inclusive units spanned by a window.
 */
export function viewportBaseCount(viewport: IntervalWindow): number {
  return Math.max(1, viewport.end - viewport.start + 1)
}

/** Upper coordinate limit of the window when its size is known. */
export function viewportEndBound(viewport: IntervalWindow): number | undefined {
  return viewport.bounds?.length
}

export interface ViewportBoundsSource {
  length: number
}

/** Whole-contig viewport for a known contig size. */
export function wholeContigViewport(
  chromosome: string,
  bounds: ViewportBoundsSource,
): GenomeViewport {
  const length = Math.max(1, bounds.length)
  return { chromosome, start: 1, end: length, bounds: { length } }
}

/**
 * Builds the initial viewport for a chromosome: the full contig when its
 * size is known, otherwise a conservative opening window.
 */
export function initialViewport(
  chromosome: string,
  options: { length?: number; defaultWindow?: number } = {},
): GenomeViewport {
  const { length, defaultWindow = 1_000_000 } = options
  if (length !== undefined && length > 0) {
    return wholeContigViewport(chromosome, { length })
  }
  return { chromosome, start: 1, end: defaultWindow, bounds: undefined }
}

/**
 * Zooms the window around its center by `factor` (values < 1 zoom in,
 * values > 1 zoom out), then clamps it to the bounds when known. Generic
 * over the window type so genome and protein viewers share one
 * implementation (see {@link IntervalWindow}).
 */
export function zoomViewport<V extends IntervalWindow>(viewport: V, factor: number): V {
  if (factor <= 0 || !Number.isFinite(factor)) return viewport

  const span = viewportBaseCount(viewport)
  const endLimit = viewportEndBound(viewport)
  const maxSpan = endLimit ?? Number.POSITIVE_INFINITY
  const clampedSpan = Math.round(Math.min(Math.max(span * factor, MIN_VIEWPORT_BASES), maxSpan))

  const center = viewport.start + Math.floor((span - 1) / 2)
  const half = Math.floor(clampedSpan / 2)

  let start = center - half
  let end = start + clampedSpan - 1

  if (start < 1) {
    start = 1
    end = start + clampedSpan - 1
  }
  if (endLimit !== undefined && end > endLimit) {
    end = endLimit
    start = Math.max(1, end - clampedSpan + 1)
  }

  return { ...viewport, start, end, bounds: viewport.bounds } as V
}

/**
 * Pans the window by `delta` units (positive = right, negative = left),
 * clamping to the valid range when known. Generic over the window type so
 * genome and protein viewers share one implementation.
 */
export function panViewport<V extends IntervalWindow>(viewport: V, delta: number): V {
  const span = viewportBaseCount(viewport)
  const endLimit = viewportEndBound(viewport)

  let start = viewport.start + delta
  let end = viewport.end + delta

  if (start < 1) {
    start = 1
    end = start + span - 1
  }
  if (endLimit !== undefined && end > endLimit) {
    end = endLimit
    start = end - span + 1
  }

  return { ...viewport, start, end, bounds: viewport.bounds } as V
}
