/**
 * Development fixtures for the Scientific Charts (Phase 6.7).
 *
 * The GenomeAI backend does **not** yet expose an expression endpoint, so
 * this module provides small, clearly isolated, typed fixtures that mimic what
 * a future expression API would return. Records flow through the same
 * normalizer (`expressionDatasetFromRecords`) the real adapter uses, so the
 * seam is exercised exactly as production would.
 *
 * ## Boundary
 *
 * These are **development fixtures, not a real API** and not scientific fact.
 * The expression values below illustrate the viewer's generic dataset model
 * (samples on the x-axis, expression values on the y-axis, one series per
 * gene) and must be replaced by real GenomeAI expression data. See
 * `docs/visualization/scientific-charts.md`.
 */

import { expressionDatasetFromRecords } from './api'
import type { ExpressionDataset } from './types'

/** Raw records for a small TP53-pathway expression demo dataset. */
const TP53_PATHWAY_EXPRESSION_RECORD = {
  id: 'expression-tp53-pathway',
  title: 'TP53 pathway expression (fixture)',
  metadata: {
    description:
      'Illustrative RNA expression across tumor and normal samples. Values are arbitrary units (fixture, not a real dataset).',
  },
  series: [
    {
      id: 'tp53',
      label: 'TP53',
      points: [
        {
          identifier: 'TP53',
          sample: 'Tumor-1',
          value: 128.4,
          normalized_value: 1.92,
          metadata: { status: 'overexpressed' },
        },
        { identifier: 'TP53', sample: 'Tumor-2', value: 142.1, normalized_value: 2.05 },
        { identifier: 'TP53', sample: 'Tumor-3', value: 119.7, normalized_value: 1.61 },
        { identifier: 'TP53', sample: 'Normal-1', value: 44.2, normalized_value: -0.31 },
        { identifier: 'TP53', sample: 'Normal-2', value: 51.8, normalized_value: -0.02 },
        { identifier: 'TP53', sample: 'Normal-3', value: 39.5, normalized_value: -0.55 },
      ],
    },
    {
      id: 'mdm2',
      label: 'MDM2',
      points: [
        { identifier: 'MDM2', sample: 'Tumor-1', value: 88.9, normalized_value: 1.22 },
        { identifier: 'MDM2', sample: 'Tumor-2', value: 96.4, normalized_value: 1.4 },
        { identifier: 'MDM2', sample: 'Tumor-3', value: 79.1, normalized_value: 0.94 },
        { identifier: 'MDM2', sample: 'Normal-1', value: 63.7, normalized_value: 0.11 },
        { identifier: 'MDM2', sample: 'Normal-2', value: 59.2, normalized_value: -0.19 },
        { identifier: 'MDM2', sample: 'Normal-3', value: 66.5, normalized_value: 0.24 },
      ],
    },
    {
      id: 'brca1',
      label: 'BRCA1',
      points: [
        { identifier: 'BRCA1', sample: 'Tumor-1', value: 32.6, normalized_value: -0.72 },
        { identifier: 'BRCA1', sample: 'Tumor-2', value: 29.4, normalized_value: -0.96 },
        { identifier: 'BRCA1', sample: 'Tumor-3', value: 35.1, normalized_value: -0.55 },
        { identifier: 'BRCA1', sample: 'Normal-1', value: 71.2, normalized_value: 0.41 },
        { identifier: 'BRCA1', sample: 'Normal-2', value: 68.9, normalized_value: 0.29 },
        { identifier: 'BRCA1', sample: 'Normal-3', value: 74.6, normalized_value: 0.52 },
      ],
    },
  ],
}

/** TP53-pathway expression demo dataset used by demos and tests. */
export const TP53_PATHWAY_EXPRESSION_FIXTURE: ExpressionDataset = expressionDatasetFromRecords(
  TP53_PATHWAY_EXPRESSION_RECORD,
) ?? {
  id: 'expression-tp53-pathway',
  title: 'TP53 pathway expression (fixture)',
  series: [],
}

/**
 * A single-series, single-point fixture covering the degenerate rendering
 * path (one sample, one series).
 */
export function buildExpressionDataset(
  overrides: {
    id?: string
    title?: string
    series?: Array<{ id: string; label: string; points: Array<[string, number]> }>
  } = {},
): ExpressionDataset {
  const series = (overrides.series ?? []).map((series) => ({
    id: series.id,
    label: series.label,
    points: series.points.map(([sample, value], index) => ({
      identifier: `${series.id}-${index + 1}`,
      sample,
      value,
    })),
  }))
  return (
    expressionDatasetFromRecords({
      id: overrides.id ?? 'expression-test',
      title: overrides.title ?? 'Test expression dataset',
      series,
    }) ?? { id: 'expression-test', title: 'Test expression dataset', series: [] }
  )
}
