/**
 * Volcano plot view-model hook (Phase 6.8).
 *
 * Composes the shared `useChartData` lifecycle with volcano derivation
 * (normalized dataset, effect-size/significance domains, highlight
 * thresholds) and point selection. The whole dataset is loaded once per
 * dataset id; thresholds and selection are client-side only.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'

import { fetchVolcanoDataset } from './advancedApi'
import type { VolcanoDataset } from './advancedTypes'
import { useChartData } from './useChartData'
import { type VolcanoDomains, hasRenderablePoints, volcanoDomains } from './volcano'

export interface VolcanoThresholds {
  /** Minimum |effect size| for the significance callout. */
  effectThreshold?: number
  /** Minimum significance for the significance callout. */
  significanceThreshold?: number
}

/** Result shape of `useVolcanoPlot`, consumed by `VolcanoPlot`. */
export interface VolcanoPlotResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the dataset load request. */
  refetch: () => void
  /** Loaded dataset, or `undefined` until success. */
  dataset: VolcanoDataset | undefined
  /** Effect-size / significance domains, or `undefined` until success. */
  domains: VolcanoDomains | undefined
  /** Thresholds used to highlight significant points. */
  thresholds: VolcanoThresholds
  /** Canonical key of the selected point (its identifier), or null. */
  selectedKey: string | null
  /** Selects a point by key; passing null clears the selection. */
  selectPoint: (key: string | null) => void
  clearSelection: () => void
}

export interface UseVolcanoPlotOptions {
  /** Fetches the dataset (defaults to `fetchVolcanoDataset(datasetId)`). */
  loader?: (signal: AbortSignal) => Promise<VolcanoDataset>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
  /** Thresholds used to highlight significant points. */
  thresholds?: VolcanoThresholds
}

const DEFAULT_THRESHOLDS: VolcanoThresholds = {
  effectThreshold: 1,
  significanceThreshold: 2,
}

export function useVolcanoPlot(options: UseVolcanoPlotOptions = {}): VolcanoPlotResult {
  const { datasetId, thresholds = DEFAULT_THRESHOLDS } = options

  const { status, data, error, refetch } = useChartData<VolcanoDataset>({
    loader: options.loader,
    datasetId,
    defaultLoader: fetchVolcanoDataset,
    noLoaderMessage: 'No volcano dataset loader provided to useVolcanoPlot.',
    isEmpty: (dataset) => !hasRenderablePoints(dataset),
  })

  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  // Clear selection whenever a new dataset loads.
  const loadedDatasetIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (data !== undefined && data.id !== loadedDatasetIdRef.current) {
      loadedDatasetIdRef.current = data.id
      setSelectedKey(null)
    }
  }, [data])

  const dataset = data
  const domains = useMemo(
    () => (dataset === undefined ? undefined : volcanoDomains(dataset)),
    [dataset],
  )

  const selectPoint = useCallback((key: string | null) => {
    setSelectedKey(key)
  }, [])

  const clearSelection = useCallback(() => setSelectedKey(null), [])

  return {
    status,
    error,
    refetch,
    dataset,
    domains,
    thresholds,
    selectedKey,
    selectPoint,
    clearSelection,
  }
}
