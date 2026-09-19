/**
 * Heatmap view-model hook (Phase 6.8).
 *
 * Composes the shared `useChartData` lifecycle with heatmap derivation
 * (normalized dataset, value domain, color scale) and cell selection. The
 * whole dataset is loaded once per dataset id; selection is client-side only,
 * so no per-view refetch is needed.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'

import { fetchHeatmapDataset } from './advancedApi'
import type { HeatmapDataset } from './advancedTypes'
import {
  type ValueDomain,
  hasRenderableValues,
  heatmapColorScale,
  heatmapValueDomain,
} from './heatmap'
import { useChartData } from './useChartData'

/** Result shape of `useHeatmap`, consumed by `Heatmap`. */
export interface HeatmapResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the dataset load request. */
  refetch: () => void
  /** Loaded dataset, or `undefined` until success. */
  dataset: HeatmapDataset | undefined
  /** Value domain over all finite matrix values (for the color scale). */
  domain: ValueDomain | undefined
  /** Maps a matrix value to a color. Defaults to a no-op for missing values. */
  colorScale: (value: number) => string
  /** Canonical key of the selected cell (`"row:column"`), or null. */
  selectedKey: string | null
  /** Selects a cell by key; passing null clears the selection. */
  selectCell: (key: string | null) => void
  clearSelection: () => void
}

export interface UseHeatmapOptions {
  /** Fetches the dataset (defaults to `fetchHeatmapDataset(datasetId)`). */
  loader?: (signal: AbortSignal) => Promise<HeatmapDataset>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
}

const FALLBACK_DOMAIN: ValueDomain = { min: -1, max: 1 }

export function useHeatmap(options: UseHeatmapOptions = {}): HeatmapResult {
  const { datasetId } = options

  const { status, data, error, refetch } = useChartData<HeatmapDataset>({
    loader: options.loader,
    datasetId,
    defaultLoader: fetchHeatmapDataset,
    noLoaderMessage: 'No heatmap dataset loader provided to useHeatmap.',
    isEmpty: (dataset) => !hasRenderableValues(dataset),
  })

  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const selectedForDatasetIdRef = useRef<string | null>(null)

  // Clear selection whenever a new dataset loads. The selection is recorded
  // alongside the dataset it belongs to so a late-running clear effect can
  // never clobber a selection made against the same dataset.
  useEffect(() => {
    if (data !== undefined && data.id !== selectedForDatasetIdRef.current) {
      selectedForDatasetIdRef.current = data.id
      setSelectedKey(null)
    }
  }, [data])

  const dataset = data
  const domain = useMemo(
    () => (dataset === undefined ? undefined : heatmapValueDomain(dataset)),
    [dataset],
  )

  const colorScale = useMemo(() => {
    const active = domain ?? FALLBACK_DOMAIN
    const scale = heatmapColorScale(active)
    return (value: number) => scale(value)
  }, [domain])

  const selectCell = useCallback(
    (key: string | null) => {
      // Record which dataset this selection belongs to so the dataset-changed
      // effect can never clear a selection made against the already-loaded
      // dataset (avoids a race with the effect running after selectCell).
      selectedForDatasetIdRef.current = data?.id ?? null
      setSelectedKey(key)
    },
    [data?.id],
  )

  const clearSelection = useCallback(() => setSelectedKey(null), [])

  return {
    status,
    error,
    refetch,
    dataset,
    domain,
    colorScale,
    selectedKey,
    selectCell,
    clearSelection,
  }
}
