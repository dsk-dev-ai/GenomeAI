/**
 * Protein Viewer view-model hook (Phase 6.5).
 *
 * Composes the Phase 6.1 visualization data lifecycle
 * (`useVisualizationData`) with pure protein viewport navigation
 * (`lib/protein/viewport.ts`) and selection state. The whole protein record
 * (sequence + features) is fetched once per protein id; pan/zoom/navigate
 * only move the residue window client-side, so no region refetch is needed.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import { ZOOM_FACTOR } from '@/lib/genome/viewport'
import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

import { fetchProtein } from './api'
import type { Protein } from './types'
import type { ProteinViewport } from './types'
import {
  initialProteinViewport,
  navigateProteinViewport,
  panFraction,
  panProteinViewport,
  zoomProteinViewport,
} from './viewport'

/** Result shape of `useProteinViewer`, consumed by `ProteinViewer`. */
export interface ProteinViewerResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the protein load request. */
  refetch: () => void
  /** Loaded protein, or `undefined` until success. */
  protein: Protein | undefined
  /** Current visible residue window. */
  viewport: ProteinViewport
  zoomIn: () => void
  zoomOut: () => void
  panLeft: () => void
  panRight: () => void
  /** Returns to the opening window. */
  resetView: () => void
  /** Jumps to an explicit 1-based inclusive residue window (clamped). */
  navigateTo: (start: number, end: number) => void
  selectedFeatureId: string | null
  /** Selects a feature (pass `null` to clear). */
  selectFeature: (featureId: string | null) => void
}

export interface UseProteinViewerOptions {
  /** Fetches the protein (defaults to `fetchProtein(proteinId)`). */
  loader?: (signal: AbortSignal) => Promise<Protein>
  /** Backend protein id used when no custom loader is provided. */
  proteinId?: string
  /** Size of the opening residue window. */
  defaultWindow?: number
  /** Feature selected when the protein first loads. */
  initialSelectedFeatureId?: string | null
}

export function useProteinViewer(options: UseProteinViewerOptions = {}): ProteinViewerResult {
  const { proteinId, defaultWindow, initialSelectedFeatureId } = options

  const loaderRef = useRef(options.loader)
  const proteinIdRef = useRef(proteinId)
  loaderRef.current = options.loader
  proteinIdRef.current = proteinId

  const loader = useCallback((signal: AbortSignal) => {
    const custom = loaderRef.current
    if (custom !== undefined) return custom(signal)
    if (proteinIdRef.current !== undefined) return fetchProtein(proteinIdRef.current, signal)
    return Promise.reject(new Error('No protein loader provided to useProteinViewer.'))
  }, [])

  const { status, data, error, refetch } = useVisualizationData<Protein>(loader, {
    isEmpty: (protein) => protein.length === 0,
  })

  const [viewport, setViewport] = useState<ProteinViewport>({ start: 1, end: 1 })
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(
    initialSelectedFeatureId ?? null,
  )

  // (Re)initialize the window when a new protein loads, so navigation always
  // starts from the opening window for the current protein.
  const loadedProteinIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (data !== undefined && data.id !== loadedProteinIdRef.current) {
      loadedProteinIdRef.current = data.id
      setViewport(initialProteinViewport(data.length, defaultWindow))
      setSelectedFeatureId(initialSelectedFeatureId ?? null)
    }
  }, [data, defaultWindow, initialSelectedFeatureId])

  const zoomIn = useCallback(() => {
    setViewport((current) => zoomProteinViewport(current, 1 / ZOOM_FACTOR))
  }, [])

  const zoomOut = useCallback(() => {
    setViewport((current) => zoomProteinViewport(current, ZOOM_FACTOR))
  }, [])

  const panLeft = useCallback(() => {
    setViewport((current) => panProteinViewport(current, panFraction(current, -1)))
  }, [])

  const panRight = useCallback(() => {
    setViewport((current) => panProteinViewport(current, panFraction(current, 1)))
  }, [])

  const resetView = useCallback(() => {
    if (data === undefined) return
    setViewport(initialProteinViewport(data.length, defaultWindow))
  }, [data, defaultWindow])

  const navigateTo = useCallback((start: number, end: number) => {
    setViewport((current) => navigateProteinViewport(current, start, end))
  }, [])

  const selectFeature = useCallback((featureId: string | null) => {
    setSelectedFeatureId(featureId)
  }, [])

  return {
    status,
    error,
    refetch,
    protein: data,
    viewport,
    zoomIn,
    zoomOut,
    panLeft,
    panRight,
    resetView,
    navigateTo,
    selectedFeatureId,
    selectFeature,
  }
}
