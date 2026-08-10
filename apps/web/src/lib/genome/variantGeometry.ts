/**
 * Pixel geometry for the variant track (Phase 6.4).
 *
 * Variants are single-position records, so their geometry is a point mark
 * on the shared Genome Browser scale (`lib/genome/geometry.ts`) rather than
 * a span. All functions map one-based-inclusive positions onto the pixel
 * canvas so the marks stay aligned with any Genome Browser axis built from
 * the same viewport. Pure functions, unit-testable without a DOM.
 */

import type { GenomeScale } from './geometry'
import type { GenomeViewport, VariantFeature } from './types'

/** Half-height of a variant mark above/below the lane centre (px). */
export const VARIANT_MARK_HALF_HEIGHT = 4

/** Vertical stride used between stacked variant marks (px). */
export const VARIANT_ROW_HEIGHT = 12

/**
 * Minimum pixel separation before two marks are treated as overlapping and
 * pushed onto separate rows, so dense regions stay readable.
 */
export const VARIANT_MIN_SEPARATION = 5

/** A variant placed in pixel space, ready for SVG rendering. */
export interface VariantMark {
  variant: VariantFeature
  /** Pixel x within the drawing area (header offset not included). */
  x: number
  /** Row index within the lane (0 = top). */
  row: number
}

/**
 * True when the variant's point lies inside the viewport on the same
 * chromosome (one-based inclusive `start <= position <= end`).
 */
export function variantInViewport(variant: VariantFeature, viewport: GenomeViewport): boolean {
  return (
    variant.chromosome === viewport.chromosome &&
    variant.position >= viewport.start &&
    variant.position <= viewport.end
  )
}

/** Keeps only variants whose single position is inside the viewport. */
export function variantsInViewport(
  variants: readonly VariantFeature[],
  viewport: GenomeViewport,
): VariantFeature[] {
  return variants.filter((variant) => variantInViewport(variant, viewport))
}

/**
 * Pixel x of a variant's point mark, without the header offset. The caller
 * adds the lane gutter so marks line up with the browser axis.
 */
export function variantX(scale: GenomeScale, position: number): number {
  return scale.toX(position)
}

/**
 * Greedy pixel-space row packing for point marks.
 *
 * Variants are sorted deterministically by position, then id. Each variant
 * is placed on the first row whose rightmost mark lies at least
 * `VARIANT_MIN_SEPARATION` pixels to the left, so adjacent or identical
 * positions never fully obscure one another. Deterministic and O(n log n).
 */
export function layoutVariantMarks(
  scale: GenomeScale,
  variants: readonly VariantFeature[],
  minSeparation: number = VARIANT_MIN_SEPARATION,
): VariantMark[] {
  const sorted = [...variants].sort((a, b) => a.position - b.position || a.id.localeCompare(b.id))

  const marks: VariantMark[] = []
  const rowEnds: number[] = []

  for (const variant of sorted) {
    const x = variantX(scale, variant.position)
    let assignedRow = -1
    for (let row = 0; row < rowEnds.length; row += 1) {
      if (x >= rowEnds[row] + minSeparation) {
        assignedRow = row
        break
      }
    }
    if (assignedRow === -1) {
      assignedRow = rowEnds.length
      rowEnds.push(0)
    }
    rowEnds[assignedRow] = Math.max(rowEnds[assignedRow], x)
    marks.push({ variant, x, row: assignedRow })
  }

  return marks
}

/**
 * Total pixel height needed for a variant lane: one row minimum, growing by
 * `VARIANT_ROW_HEIGHT` per extra row so stacked marks never clip.
 */
export function variantTrackHeight(rowCount: number): number {
  return Math.max(1, rowCount) * VARIANT_ROW_HEIGHT
}

/** Pixel y of a stacked row's centre line within the lane. */
export function variantRowY(row: number): number {
  return row * VARIANT_ROW_HEIGHT + VARIANT_ROW_HEIGHT / 2
}
