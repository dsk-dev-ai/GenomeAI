/**
 * Development fixtures for the Advanced Scientific Charts (Phase 6.8).
 *
 * The GenomeAI backend does **not** yet expose heatmap, volcano, coverage, or
 * distribution endpoints, so this module provides small, clearly isolated,
 * typed fixtures that mimic what future endpoints would return. Records flow
 * through the same normalizers (`heatmapFromRecords`, `volcanoFromRecords`,
 * `coverageFromRecords`, `distributionFromRecords`) the real adapters use, so
 * every seam is exercised exactly as production would.
 *
 * ## Boundary
 *
 * These are **development fixtures, not a real API** and not scientific fact.
 * Every dataset is explicitly titled "fixture" and the values only illustrate
 * each chart's generic data model. They must be replaced by real GenomeAI
 * data. See `docs/visualization/advanced-scientific-charts.md`.
 */

import {
  coverageFromRecords,
  distributionFromRecords,
  heatmapFromRecords,
  volcanoFromRecords,
} from './advancedApi'
import type {
  CoverageDataset,
  DistributionDataset,
  HeatmapDataset,
  VolcanoDataset,
} from './advancedTypes'

/** Raw records for a small TP53-pathway expression heatmap demo dataset. */
const TP53_PATHWAY_HEATMAP_RECORD = {
  id: 'heatmap-tp53-pathway',
  title: 'TP53 pathway heatmap (fixture)',
  metadata: {
    description:
      'Illustrative z-scored expression across tumor and normal samples. Values are arbitrary units (fixture, not a real dataset).',
  },
  rows: ['tp53', 'mdm2', 'brca1'],
  columns: ['Tumor-1', 'Tumor-2', 'Tumor-3', 'Normal-1', 'Normal-2', 'Normal-3'],
  values: [
    [1.92, 2.05, 1.61, -0.31, -0.02, -0.55],
    [1.22, 1.4, 0.94, 0.11, -0.19, 0.24],
    [-0.72, -0.96, -0.55, 0.41, 0.29, 0.52],
  ],
  row_labels: { tp53: 'TP53', mdm2: 'MDM2', brca1: 'BRCA1' },
}

/** TP53-pathway heatmap demo dataset used by demos and tests. */
export const TP53_PATHWAY_HEATMAP_FIXTURE: HeatmapDataset = heatmapFromRecords(
  TP53_PATHWAY_HEATMAP_RECORD,
) ?? {
  id: 'heatmap-tp53-pathway',
  title: 'TP53 pathway heatmap (fixture)',
  rows: [],
  columns: [],
  values: [],
}

/** Raw records for a small differential-expression volcano demo dataset. */
const DIFFERENTIAL_EXPRESSION_VOLCANO_RECORD = {
  id: 'volcano-differential-expression',
  title: 'Differential expression volcano (fixture)',
  metadata: {
    description:
      'Illustrative log2 fold changes and significance scores. Effect sizes and significance are arbitrary units (fixture, not a real dataset).',
  },
  points: [
    {
      identifier: 'TP53',
      effect_size: 1.6,
      significance: 4.2,
      adjusted_significance: 3.1,
      metadata: { status: 'up' },
    },
    { identifier: 'MDM2', effect_size: 0.9, significance: 2.4, adjusted_significance: 1.9 },
    { identifier: 'BRCA1', effect_size: -1.2, significance: 3.5, adjusted_significance: 2.8 },
    { identifier: 'GATA3', effect_size: 2.1, significance: 5.8, adjusted_significance: 4.6 },
    { identifier: 'ESR1', effect_size: -0.4, significance: 0.8 },
    { identifier: 'MYC', effect_size: 0.3, significance: 1.1 },
    { identifier: 'PTEN', effect_size: -1.8, significance: 4.9, adjusted_significance: 3.9 },
    { identifier: 'KRAS', effect_size: 0.2, significance: 0.6 },
    { identifier: 'EGFR', effect_size: 1.1, significance: 2.1, adjusted_significance: 1.7 },
    { identifier: 'ATM', effect_size: -0.7, significance: 1.6 },
    { identifier: 'CHEK2', effect_size: 0.5, significance: 1.4 },
    { identifier: 'RB1', effect_size: -2.3, significance: 6.2, adjusted_significance: 5.1 },
  ],
}

/** Differential-expression volcano demo dataset used by demos and tests. */
export const DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE: VolcanoDataset = volcanoFromRecords(
  DIFFERENTIAL_EXPRESSION_VOLCANO_RECORD,
) ?? {
  id: 'volcano-differential-expression',
  title: 'Differential expression volcano (fixture)',
  points: [],
}

/** Raw records for a small coverage demo dataset over the TP53 window. */
const TP53_WINDOW_COVERAGE_RECORD = {
  id: 'coverage-tp53-window',
  title: 'TP53 window coverage (fixture)',
  metadata: {
    description:
      'Illustrative per-bin read depth across the TP53 neighbourhood. Depths are arbitrary units (fixture, not a real dataset).',
  },
  bins: [
    { chromosome: 'chr17', start: 7668402, end: 7668513, coverage: 32 },
    { chromosome: 'chr17', start: 7668514, end: 7668625, coverage: 41 },
    { chromosome: 'chr17', start: 7668626, end: 7668737, coverage: 35 },
    { chromosome: 'chr17', start: 7668738, end: 7668849, coverage: 22 },
    { chromosome: 'chr17', start: 7668850, end: 7668961, coverage: 18 },
    { chromosome: 'chr17', start: 7668962, end: 7669073, coverage: 26 },
    { chromosome: 'chr17', start: 7669074, end: 7669185, coverage: 48 },
    { chromosome: 'chr17', start: 7669186, end: 7669297, coverage: 53 },
    { chromosome: 'chr17', start: 7669298, end: 7669409, coverage: 47 },
    { chromosome: 'chr17', start: 7669410, end: 7669521, coverage: 61 },
    { chromosome: 'chr17', start: 7669522, end: 7669633, coverage: 58 },
    { chromosome: 'chr17', start: 7669634, end: 7669745, coverage: 39 },
    { chromosome: 'chr17', start: 7669746, end: 7669857, coverage: 44 },
    { chromosome: 'chr17', start: 7669858, end: 7669969, coverage: 51 },
    { chromosome: 'chr17', start: 7669970, end: 7670081, coverage: 63 },
    { chromosome: 'chr17', start: 7670082, end: 7670193, coverage: 57 },
    { chromosome: 'chr17', start: 7670194, end: 7670305, coverage: 33 },
    { chromosome: 'chr17', start: 7670306, end: 7670417, coverage: 29 },
    { chromosome: 'chr17', start: 7670418, end: 7670529, coverage: 24 },
    { chromosome: 'chr17', start: 7670530, end: 7670641, coverage: 27 },
  ],
}

/** TP53-window coverage demo dataset used by demos and tests. */
export const TP53_WINDOW_COVERAGE_FIXTURE: CoverageDataset = coverageFromRecords(
  TP53_WINDOW_COVERAGE_RECORD,
) ?? {
  id: 'coverage-tp53-window',
  title: 'TP53 window coverage (fixture)',
  bins: [],
}

/** Raw records for a small distribution demo dataset across conditions. */
const EXPRESSION_DISTRIBUTION_RECORD = {
  id: 'distribution-expression-by-condition',
  title: 'Expression distribution by condition (fixture)',
  metadata: {
    description:
      'Illustrative expression values grouped by condition. Values are arbitrary units (fixture, not a real dataset).',
  },
  values: [
    { group: 'Tumor', value: 128.4 },
    { group: 'Tumor', value: 142.1 },
    { group: 'Tumor', value: 119.7 },
    { group: 'Tumor', value: 135.2 },
    { group: 'Tumor', value: 111.8 },
    { group: 'Tumor', value: 88.9 },
    { group: 'Tumor', value: 96.4 },
    { group: 'Tumor', value: 79.1 },
    { group: 'Normal', value: 44.2 },
    { group: 'Normal', value: 51.8 },
    { group: 'Normal', value: 39.5 },
    { group: 'Normal', value: 63.7 },
    { group: 'Normal', value: 59.2 },
    { group: 'Normal', value: 66.5 },
    { group: 'Normal', value: 71.2 },
    { group: 'Normal', value: 68.9 },
    { group: 'Normal', value: 74.6 },
  ],
}

/** Expression-by-condition distribution demo dataset used by demos/tests. */
export const EXPRESSION_DISTRIBUTION_FIXTURE: DistributionDataset = distributionFromRecords(
  EXPRESSION_DISTRIBUTION_RECORD,
) ?? {
  id: 'distribution-expression-by-condition',
  title: 'Expression distribution by condition (fixture)',
  values: [],
}
