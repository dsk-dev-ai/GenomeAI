/**
 * Distribution chart view-model hook (Phase 6.8).
 *
 * Composes the shared `useChartData` lifecycle with distribution derivation
 * (groups, value domain, per-group summary statistics and whiskers). The
 * whole dataset is loaded once per dataset id; there is no per-view
 * selection state because the distribution chart is driven by its summary
 * statistics rather than individual marks.
 */

import { useMemo } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'

import { fetchDistributionDataset } from './advancedApi'
import type { DistributionDataset } from './advancedTypes'
import {
  distributionGroups,
  groupStatistics,
  groupWhiskers,
  hasRenderableValues,
} from './distribution'
import type { SummaryStatistics, Whiskers } from './statistics'
import { useChartData } from './useChartData'

export interface GroupStatistics {
  group: string
  summary: SummaryStatistics | undefined
  whiskers: Whiskers | undefined
}

export interface ValueDomain {
  min: number
  max: number
}

/** Result shape of `useDistributionChart`, consumed by `DistributionChart`. */
export interface DistributionChartResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the dataset load request. */
  refetch: () => void
  /** Loaded dataset, or `undefined` until success. */
  dataset: DistributionDataset | undefined
  /** Sorted group names driving the x-axis (empty until success). */
  groups: string[]
  /** Per-group summary statistics, aligned with `groups`. */
  statistics: GroupStatistics[]
  /** Value domain across all groups (for the y-axis). */
  valueDomain: ValueDomain
}

export interface UseDistributionChartOptions {
  /** Fetches the dataset (defaults to `fetchDistributionDataset(datasetId)`). */
  loader?: (signal: AbortSignal) => Promise<DistributionDataset>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
}

const EMPTY_DOMAIN: ValueDomain = { min: 0, max: 1 }

export function useDistributionChart(
  options: UseDistributionChartOptions = {},
): DistributionChartResult {
  const { datasetId } = options

  const { status, data, error, refetch } = useChartData<DistributionDataset>({
    loader: options.loader,
    datasetId,
    defaultLoader: fetchDistributionDataset,
    noLoaderMessage: 'No distribution dataset loader provided to useDistributionChart.',
    isEmpty: (dataset) => !hasRenderableValues(dataset),
  })

  const groups = useMemo(() => (data === undefined ? [] : distributionGroups(data)), [data])

  const statistics = useMemo<GroupStatistics[]>(
    () =>
      data === undefined
        ? []
        : groups.map((group) => ({
            group,
            summary: groupStatistics(data, group),
            whiskers: groupWhiskers(data, group),
          })),
    [data, groups],
  )

  const valueDomain = useMemo<ValueDomain>(() => {
    if (statistics.length === 0) return EMPTY_DOMAIN
    let min = Number.POSITIVE_INFINITY
    let max = Number.NEGATIVE_INFINITY
    let found = false
    for (const entry of statistics) {
      const summary = entry.summary
      if (summary === undefined) continue
      const candidates: number[] = [summary.min, summary.max, summary.q1, summary.q3]
      if (entry.whiskers !== undefined) {
        candidates.push(entry.whiskers.lower, entry.whiskers.upper)
        for (const outlier of entry.whiskers.outliers) candidates.push(outlier)
      }
      for (const value of candidates) {
        if (value < min) min = value
        if (value > max) max = value
        found = true
      }
    }
    if (!found) return EMPTY_DOMAIN
    if (min === max) {
      const pad = Math.max(1, Math.abs(max) * 0.5)
      return { min: min - pad, max: max + pad }
    }
    return { min, max }
  }, [statistics])

  return {
    status,
    error,
    refetch,
    dataset: data,
    groups,
    statistics,
    valueDomain,
  }
}
