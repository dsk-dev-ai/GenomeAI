/**
 * Pixel geometry for the Protein Viewer (Phase 6.5).
 *
 * Maps one-based-inclusive residue positions onto the pixel canvas using the
 * shared Genome Browser scale (`lib/genome/geometry.ts`) and the shared
 * interval-clipping helper (`intervalToPixels`), so feature bars and residue
 * letters align with each other and stay consistent with the genome viewers.
 * Feature row packing reuses the genome `layoutRows` algorithm. Pure
 * functions, unit-testable without a DOM.
 */

import { createScale, intervalToPixels, niceTickStep } from '@/lib/genome/geometry'
import type { GenomeScale } from '@/lib/genome/geometry'
import { layoutRows } from '@/lib/genome/tracks'
import type { FeatureRow } from '@/lib/genome/tracks'

import type { ProteinFeature, ProteinViewport } from './types'

/** Pixel width of the SVG drawing area used as the `viewBox` base. */
export const SVG_WIDTH = 1000

/** Pixel width of the left label gutter shared by all lanes. */
export const LABEL_GUTTER = 96

/** Vertical stride used between stacked feature rows. */
export const FEATURE_ROW_HEIGHT = 18

/** Pixel height reserved for the residue-sequence lane. */
export const SEQUENCE_ROW_HEIGHT = 26

/** Pixel height reserved for the residue-number axis. */
export const AXIS_HEIGHT = 20

/** Pixels per residue required before per-residue letters are rendered. */
export const RESIDUE_LABEL_MIN_PX = 6

/** Pixels per residue that is treated as fully zoomed-in for font sizing. */
export const RESIDUE_LABEL_MAX_PX = 14

/** Builds a scale mapping a residue window into `width` pixels. */
export function createResidueScale(
  viewport: ProteinViewport,
  width: number = SVG_WIDTH - LABEL_GUTTER,
): GenomeScale {
  return createScale(viewport.start, viewport.end, width)
}

/** True when the feature interval overlaps the viewport. */
export function featureInViewport(feature: ProteinFeature, viewport: ProteinViewport): boolean {
  return feature.start <= viewport.end && feature.end >= viewport.start
}

/** Keeps only features that overlap the visible residue window. */
export function featuresInViewport(
  features: readonly ProteinFeature[],
  viewport: ProteinViewport,
): ProteinFeature[] {
  return features.filter((feature) => featureInViewport(feature, viewport))
}

/** Rendered pixel geometry of a feature bar, clipped to the viewport. */
export function featureToPixels(
  scale: GenomeScale,
  viewport: ProteinViewport,
  feature: ProteinFeature,
) {
  return intervalToPixels(scale, viewport, feature.start, feature.end)
}

/** Pixel x of the left edge of a residue's cell (header offset not added). */
export function residueX(scale: GenomeScale, index: number): number {
  return scale.toX(index)
}

/** Pixel x of a residue cell's centre. */
export function residueCenterX(scale: GenomeScale, index: number): number {
  return scale.toX(index) + scale.pxPerBase / 2
}

/** Pixel x of a residue number label (centred on its cell). */
export function residueLabelX(scale: GenomeScale, index: number): number {
  return residueCenterX(scale, index)
}

/**
 * Greedy non-overlap row packing for protein features (identical semantics
 * to the genome track row packing). Deterministic and O(n log n).
 */
export function layoutFeatureRows(
  features: readonly ProteinFeature[],
): FeatureRow<ProteinFeature>[] {
  return layoutRows(features)
}

/**
 * Total pixel height of the viewer SVG: residue axis, feature rows, and the
 * sequence lane.
 */
export function proteinViewerHeight(featureRowCount: number): number {
  return AXIS_HEIGHT + featureRowCount * FEATURE_ROW_HEIGHT + SEQUENCE_ROW_HEIGHT
}

/** Pixel y of the sequence lane's baseline within the SVG. */
export function sequenceRowY(featureRowCount: number): number {
  return AXIS_HEIGHT + featureRowCount * FEATURE_ROW_HEIGHT
}

/** Font size (px) for residue letters at a given pixels-per-residue. */
export function residueFontSize(pxPerResidue: number): number {
  const clamped = Math.max(RESIDUE_LABEL_MIN_PX, Math.min(pxPerResidue, RESIDUE_LABEL_MAX_PX))
  return Math.round(clamped * 0.8)
}

/** An axis tick over residue positions. */
export interface ResidueTick {
  position: number
  label: string
  major: boolean
}

/**
 * Major labelled residue ticks plus unlabelled minor ticks across a
 * one-based-inclusive residue window. Reuses the genome `niceTickStep` so
 * spacing is familiar, but labels are plain integers (no K/M suffixes).
 */
export function computeResidueTicks(
  start: number,
  end: number,
  targetTicks = 8,
  minorPerMajor = 4,
): ResidueTick[] {
  const residues = Math.max(1, end - start + 1)
  const targetStep = residues / targetTicks
  const majorStep = niceTickStep(targetStep, 1)
  const divisions = Math.max(1, Math.floor(minorPerMajor))
  const minorStep = Math.max(1, Math.floor(majorStep / divisions))

  const ticks: ResidueTick[] = []
  const firstMajor = Math.ceil(start / majorStep) * majorStep
  const lastMajor = Math.floor(end / majorStep) * majorStep

  const minorStart = Math.max(Math.floor(start / minorStep) * minorStep, start)
  const minorEnd = Math.min(Math.ceil(end / minorStep) * minorStep, end)
  for (let pos = minorStart; pos <= minorEnd; pos += minorStep) {
    if (pos >= firstMajor && pos <= lastMajor && pos % majorStep === 0) continue
    ticks.push({ position: pos, label: '', major: false })
  }

  for (let pos = firstMajor; pos <= lastMajor; pos += majorStep) {
    ticks.push({ position: pos, label: formatResiduePosition(pos), major: true })
  }

  ticks.sort((a, b) => a.position - b.position)
  return ticks
}

/** Formats a residue position as a plain grouped integer, e.g. `1,234`. */
export function formatResiduePosition(position: number): string {
  return position.toLocaleString('en-US')
}
