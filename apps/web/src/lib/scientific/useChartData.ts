/**
 * Shared chart data lifecycle hook (Phase 6.8).
 *
 * Every scientific chart hook (expression, heatmap, volcano, coverage,
 * distribution) follows the same data pattern: an optional custom loader that
 * takes precedence, a dataset-id-scoped default loader for the (not yet
 * existing) backend endpoints, a reload whenever the requested dataset id
 * changes, and the loading / empty / success / error lifecycle from
 * `useVisualizationData`. This hook owns that shared pattern so chart hooks
 * only implement their own derivation and selection logic.
 */

import { useCallback, useEffect, useRef } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

export interface UseChartDataOptions<T> {
  /** Fetches the dataset; takes precedence over `defaultLoader`. */
  loader?: (signal: AbortSignal) => Promise<T>
  /**
   * Fetches a dataset by id when no custom loader is given. Backend
   * endpoints are not implemented yet, so the default loader throws a typed
   * `GenomeApiError` today (see `lib/scientific/api.ts`).
   */
  defaultLoader?: (datasetId: string, signal: AbortSignal) => Promise<T>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
  /** Message used when neither a loader nor a dataset id is available. */
  noLoaderMessage?: string
  /** Predicate applied to a successful load; true => `empty` status. */
  isEmpty?: (data: T) => boolean
}

export interface UseChartDataResult<T> {
  status: VisualizationStatus
  data: T | undefined
  error: VisualizationError | undefined
  /** Re-runs the load request. */
  refetch: () => void
}

export function useChartData<T>(options: UseChartDataOptions<T> = {}): UseChartDataResult<T> {
  const { datasetId, isEmpty } = options

  const loaderRef = useRef(options.loader)
  const defaultLoaderRef = useRef(options.defaultLoader)
  const noLoaderMessageRef = useRef(options.noLoaderMessage)
  loaderRef.current = options.loader
  defaultLoaderRef.current = options.defaultLoader
  noLoaderMessageRef.current = options.noLoaderMessage

  const datasetIdRef = useRef(datasetId)
  datasetIdRef.current = datasetId

  const loader = useCallback((signal: AbortSignal) => {
    const custom = loaderRef.current
    if (custom !== undefined) return custom(signal)
    if (datasetIdRef.current !== undefined && defaultLoaderRef.current !== undefined) {
      return defaultLoaderRef.current(datasetIdRef.current, signal)
    }
    const message = noLoaderMessageRef.current ?? 'No chart data loader provided to the chart hook.'
    return Promise.reject(new Error(message))
  }, [])

  const { status, data, error, refetch } = useVisualizationData<T>(loader, { isEmpty })

  // Reload whenever the requested dataset id changes. The loader reads the
  // latest `datasetId` through a ref, but `useVisualizationData` only fetches
  // on mount, so a changed id would otherwise silently keep the old data.
  const previousDatasetIdRef = useRef(datasetId)
  useEffect(() => {
    if (previousDatasetIdRef.current !== datasetId) {
      previousDatasetIdRef.current = datasetId
      refetch()
    }
  }, [datasetId, refetch])

  return { status, data, error, refetch }
}
