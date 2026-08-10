/**
 * Minimal track architecture for the Genome Browser (Phase 6.2).
 *
 * A track is a named lane that receives one class of genomic feature and
 * renders it in a consistent lane. This milestone ships the blueprint plus
 * two concrete tracks — genes and variants — to prove the architecture.
 * Later milestones (6.3 transcripts, 6.4 variants in depth, regulatory
 * regions, annotations) extend the same interface without re-plumbing the
 * browser.
 *
 * Layout is expressed as pure functions so chunks are unit-testable and
 * the SVG renderer stays thin.
 */

import type { GenomeViewport, GenomicFeature } from './types'

export type TrackKind = 'genes' | 'variants'

/** Definition of a renderable track provided to the browser. */
export interface GenomeTrack {
  /** Stable track id. */
  id: string
  /** Display label, e.g. `Genes`. */
  label: string
  /** The rendering strategy / colour scheme to use. */
  kind: TrackKind
  /** Toggles visibility without re-fetching. */
  visible: boolean
}

/** Configuration for the built-in tracks. */
export interface GenomeTrackConfig {
  enabled: Record<TrackKind, boolean>
}

/** The Genome Browser’s default track set. */
export const DEFAULT_TRACK_CONFIG: GenomeTrackConfig = {
  enabled: { genes: true, variants: true },
}

/** Per-row vertical stride (px) used by `layoutRows`. */
export const TRACK_ROW_HEIGHT = 16

/** A non-overlapping row produced by {@link layoutRows}. */
export interface FeatureRow {
  features: GenomicFeature[]
  /** Vertical offset (px) from the track top. */
  yOffset: number
}

/**
 * Greedy non-overlap row packing: assigns each feature to the first row
 * whose rightmost end lies before the feature's start. Results are
 * deterministic (stable sort by start, then end, then id) and O(n log n).
 * This is intentionally not optimal packing — visualizations only need a
 * deterministic, readable arrangement.
 */
export function layoutRows(features: readonly GenomicFeature[]): FeatureRow[] {
  const sorted = [...features].sort(
    (a, b) => a.start - b.start || a.end - b.end || a.id.localeCompare(b.id),
  )

  const rows: FeatureRow[] = []
  const rowEnds: number[] = []

  for (const feature of sorted) {
    let assignedRow = -1
    for (let r = 0; r < rows.length; r += 1) {
      if (feature.start > rowEnds[r]) {
        assignedRow = r
        break
      }
    }
    if (assignedRow === -1) {
      assignedRow = rows.length
      rows.push({ features: [], yOffset: rows.length * TRACK_ROW_HEIGHT })
      rowEnds.push(0)
    }
    rows[assignedRow].features.push(feature)
    rowEnds[assignedRow] = Math.max(rowEnds[assignedRow], feature.end)
  }

  return rows
}

/**
 * One-based inclusive overlap test used to keep only features intersecting
 * the viewport (`a.start <= b.end && a.end >= b.start`). Also requires the
 * feature to be on the same chromosome, so a feature with numerically
 * overlapping coordinates cannot leak in from a different contig.
 */
export function featuresInViewport(
  features: readonly GenomicFeature[],
  viewport: GenomeViewport,
): GenomicFeature[] {
  const { chromosome, start, end } = viewport
  return features.filter(
    (feature) => feature.chromosome === chromosome && feature.start <= end && feature.end >= start,
  )
}
