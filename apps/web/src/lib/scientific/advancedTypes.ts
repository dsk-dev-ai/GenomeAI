/**
 * Advanced scientific chart data models (Phase 6.8).
 *
 * Strongly typed dataset shapes for the four advanced charts built on top of
 * the Phase 6.7 scientific foundation (heatmap, volcano, coverage,
 * distribution). Like `lib/scientific/types.ts` these models describe the
 * *data* only — every rendering concern (scales, axes, tooltips, selection)
 * is derived by the pure modules under `lib/scientific` and composed by the
 * view-model hooks under `lib/scientific/use*Chart.ts`.
 *
 * The models deliberately reuse `ScientificMetadata` and the Phase 6.2
 * one-based inclusive coordinate conventions from `lib/genome/types.ts`.
 */

import type { ScientificMetadata } from './types'

/**
 * A heatmap measurement matrix.
 *
 * `rows` and `columns` are the stable identifiers of the row and column
 * axes (e.g. samples and genes). `values[rowIndex][columnIndex]` holds the
 * measured value; `undefined` means "no measurement" (rendered as a missing
 * cell, never as zero). `rowLabels`/`columnLabels` map an axis identifier to
 * an optional display name that overrides the raw identifier.
 */
export interface HeatmapDataset {
  id: string
  title: string
  /** Row identifiers; `rows[r]` labels the r-th row of `values`. */
  rows: string[]
  /** Column identifiers; `columns[c]` labels the c-th column of `values`. */
  columns: string[]
  /** `values[r][c]` is the measurement for `rows[r]` × `columns[c]`. */
  values: Array<Array<number | undefined>>
  /** Optional display name per row id. */
  rowLabels?: Record<string, string>
  /** Optional display name per column id. */
  columnLabels?: Record<string, string>
  metadata?: ScientificMetadata
}

/**
 * One feature tested for differential regulation (Phase 6.8 volcano plot).
 *
 * `identifier` is the stable id of the measured feature (e.g. a gene).
 * `effectSize` is the magnitude/direction of the change (e.g. log2 fold
 * change) and `significance` is the y-axis measure of evidence (e.g.
 * `-log10(p)`), where larger values mean stronger evidence. The chart treats
 * both as plain numbers and never assumes their units. `adjustedSignificance`
 * is an optional multiple-testing-corrected value surfaced in tooltips only.
 */
export interface VolcanoPoint {
  identifier: string
  /** Direction and magnitude of the change (e.g. log2 fold change). */
  effectSize: number
  /** Evidence measure; larger = more significant (e.g. -log10(p)). */
  significance: number
  /** Optional multiple-testing-corrected significance (tooltip only). */
  adjustedSignificance?: number
  metadata?: ScientificMetadata
}

/** A volcano plot dataset: a set of tested features. */
export interface VolcanoDataset {
  id: string
  title: string
  points: VolcanoPoint[]
  metadata?: ScientificMetadata
}

/**
 * One coverage measurement over a one-based inclusive genomic interval.
 *
 * `chromosome` is the reference contig, and `start`/`end` follow the Phase
 * 6.2 inclusive convention (`length = end - start + 1`, `start >= 1`).
 * `coverage` is the depth observed across the interval.
 */
export interface CoverageBin {
  chromosome: string
  /** 1-based inclusive start. */
  start: number
  /** 1-based inclusive end. */
  end: number
  /** Observed coverage depth across the interval. */
  coverage: number
  metadata?: ScientificMetadata
}

/** A coverage dataset: depth measurements over genomic intervals. */
export interface CoverageDataset {
  id: string
  title: string
  bins: CoverageBin[]
  metadata?: ScientificMetadata
}

/**
 * One value grouped under a category (Phase 6.8 distribution chart).
 *
 * `group` is the categorical dimension shown on the x-axis (e.g. a sample,
 * treatment, or condition) and `value` is one measurement within that group.
 * Summary statistics (quartiles, whiskers, outliers) are derived from the
 * grouped values by `lib/scientific/statistics.ts`.
 */
export interface DistributionValue {
  group: string
  value: number
  metadata?: ScientificMetadata
}

/** A distribution dataset: grouped numeric measurements. */
export interface DistributionDataset {
  id: string
  title: string
  values: DistributionValue[]
  metadata?: ScientificMetadata
}
