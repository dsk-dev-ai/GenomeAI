/**
 * Expression Chart view-model hook (Phase 6.7).
 *
 * Composes the Phase 6.1 visualization data lifecycle
 * (`useVisualizationData`) with dataset derivation (samples, active value
 * field, y-domain) and point selection. The whole dataset is loaded once per
 * dataset id; the value-field toggle and selection are client-side only, so
 * no per-view refetch is needed.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

import { fetchExpressionDataset } from './api'
import {
  type ExpressionValueField,
  availableSamples,
  expressionValueDomain,
  hasNormalizedValues,
  hasRenderablePoints,
} from './expression'
import type { ExpressionDataset } from './types'

/** Result shape of `useExpressionChart`, consumed by `ExpressionChart`. */
export interface ExpressionChartResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the dataset load request. */
  refetch: () => void
  /** Loaded dataset, or `undefined` until success. */
  dataset: ExpressionDataset | undefined
  /** Sorted sample names driving the x-axis (empty until success). */
  samples: string[]
  /** The y-axis value field in use. */
  valueField: ExpressionValueField
  /** Switches the y-axis between raw and normalized values. */
  setValueField: (field: ExpressionValueField) => void
  /** True when at least one point has a normalized value. */
  hasNormalizedValues: boolean
  /** Y-axis domain for the active field (always finite, non-empty). */
  valueDomain: { min: number; max: number }
  /** Canonical key of the selected point (`"seriesId:pointId"`), or null. */
  selectedKey: string | null
  /** Selects a point by key; passing null clears the selection. */
  selectPoint: (key: string | null) => void
  clearSelection: () => void
}

export interface UseExpressionChartOptions {
  /** Fetches the dataset (defaults to `fetchExpressionDataset(datasetId)`). */
  loader?: (signal: AbortSignal) => Promise<ExpressionDataset>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
}

const EMPTY_DOMAIN = { min: 0, max: 1 }

export function useExpressionChart(options: UseExpressionChartOptions = {}): ExpressionChartResult {
  const { datasetId } = options

  const loaderRef = useRef(options.loader)
  const datasetIdRef = useRef(datasetId)
  loaderRef.current = options.loader
  datasetIdRef.current = datasetId

  const loader = useCallback((signal: AbortSignal) => {
    const custom = loaderRef.current
    if (custom !== undefined) return custom(signal)
    if (datasetIdRef.current !== undefined)
      return fetchExpressionDataset(datasetIdRef.current, signal)
    return Promise.reject(new Error('No expression dataset loader provided to useExpressionChart.'))
  }, [])

  const { status, data, error, refetch } = useVisualizationData<ExpressionDataset>(loader, {
    isEmpty: (dataset) => dataset.series.length === 0 || !hasRenderablePoints(dataset),
  })

  const dataset = data

  const samples = useMemo(() => (dataset === undefined ? [] : availableSamples(dataset)), [dataset])

  const normalizedAvailable = useMemo(
    () => (dataset === undefined ? false : hasNormalizedValues(dataset)),
    [dataset],
  )

  const [valueField, setValueField] = useState<ExpressionValueField>('value')
  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  // Clear selection whenever a new dataset loads.
  const loadedDatasetIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (dataset !== undefined && dataset.id !== loadedDatasetIdRef.current) {
      loadedDatasetIdRef.current = dataset.id
      setSelectedKey(null)
    }
  }, [dataset])

  // Fall back to raw values when normalized values are not available.
  const effectiveField: ExpressionValueField =
    valueField === 'normalizedValue' && !normalizedAvailable ? 'value' : valueField

  const valueDomain = useMemo(
    () => (dataset === undefined ? EMPTY_DOMAIN : expressionValueDomain(dataset, effectiveField)),
    [dataset, effectiveField],
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
    samples,
    valueField: effectiveField,
    setValueField,
    hasNormalizedValues: normalizedAvailable,
    valueDomain,
    selectedKey,
    selectPoint,
    clearSelection,
  }
}
