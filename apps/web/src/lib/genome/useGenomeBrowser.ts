/**
 * Genome Browser state hook (Phase 6.2).
 *
 * Composes the pure viewport math (`lib/genome/viewport.ts`) with the
 * Phase 6.1 data layer (`useVisualizationData`). Navigation and data
 * fetching are deliberately decoupled: navigation only mutates viewport
 * state, while per-track loaders (which accept an `AbortSignal`) fetch
 * only the currently visible region.
 *
 * Region changes are debounced (default 300 ms) so rapid pan/zoom does not
 * fire a request per animation frame.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import type { VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

import type { TrackKind } from './tracks'
import type { GenomeViewport, GenomicFeature, GenomicInterval } from './types'
import { PAN_FRACTION, ZOOM_FACTOR, panViewport, viewportBaseCount, zoomViewport } from './viewport'

/** Loads a track's visible features for a one-based inclusive interval. */
export type GenomeTrackLoader = (
  interval: GenomicInterval,
  signal: AbortSignal,
) => Promise<GenomicFeature[]>

/** Definition of a visible track (kind maps to rendering + colours). */
export interface GenomeTrackDefinition {
  id: string
  label: string
  kind: TrackKind
  loader: GenomeTrackLoader
}

/** A track's data-layer result, keyed by `id`. */
export interface GenomeTrackData extends GenomeTrackDefinition {
  status: VisualizationStatus
  data: GenomicFeature[] | undefined
  /** Present when `status === 'error'`. */
  errorMessage: string | undefined
  /** Re-runs the track's request (used by the retry UI). */
  refetch: () => void
}

export interface GenomeBrowserOptions {
  /** Viewport shown on first render. */
  initialViewport: GenomeViewport
  /** Tracks to fetch and render. */
  tracks: GenomeTrackDefinition[]
  /** Debounce (ms) applied to viewport changes before refetching. */
  debounceMs?: number
}

export interface GenomeBrowserResult {
  /** Current, immutable viewport. */
  viewport: GenomeViewport
  /** Per-track data layer results, in `tracks` order. */
  trackResults: GenomeTrackData[]
  zoomIn: () => void
  zoomOut: () => void
  panLeft: () => void
  panRight: () => void
  reset: () => void
  /** Jumps to an explicit region (from the region input). */
  navigateTo: (interval: GenomicInterval) => void
}

function useDebouncedViewport(viewport: GenomeViewport, debounceMs: number): GenomeViewport {
  const [debounced, setDebounced] = useState(viewport)
  const first = useRef(true)

  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    const timer = window.setTimeout(() => setDebounced(viewport), debounceMs)
    return () => window.clearTimeout(timer)
  }, [viewport, debounceMs])

  return debounced
}

function useGenomeTrack(
  definition: GenomeTrackDefinition,
  debouncedViewport: GenomeViewport,
): GenomeTrackData {
  const definitionRef = useRef(definition)
  definitionRef.current = definition

  const viewportRef = useRef(debouncedViewport)
  viewportRef.current = debouncedViewport

  const loader = useCallback(
    (signal: AbortSignal) =>
      definitionRef.current.loader(
        {
          chromosome: viewportRef.current.chromosome,
          start: viewportRef.current.start,
          end: viewportRef.current.end,
        },
        signal,
      ),
    [],
  )
  const isEmpty = useCallback((features: GenomicFeature[]) => features.length === 0, [])

  const { status, data, error, refetch } = useVisualizationData<GenomicFeature[]>(loader, {
    isEmpty,
  })

  // Refetch when the (debounced) viewport settles on a new chromosome or
  // window. `useVisualizationData` already fired the initial request with the
  // initial viewport, so skip the first run.
  const regionKey = `${debouncedViewport.chromosome}:${debouncedViewport.start}-${debouncedViewport.end}`
  const lastRegionKey = useRef<string | null>(null)
  useEffect(() => {
    if (lastRegionKey.current === null) {
      lastRegionKey.current = regionKey
      return
    }
    if (lastRegionKey.current !== regionKey) {
      lastRegionKey.current = regionKey
      refetch()
    }
  }, [refetch, regionKey])

  return {
    id: definition.id,
    label: definition.label,
    kind: definition.kind,
    loader: definition.loader,
    status,
    data,
    errorMessage: error?.message,
    refetch,
  }
}

export function useGenomeBrowser(options: GenomeBrowserOptions): GenomeBrowserResult {
  const { initialViewport, tracks, debounceMs = 300 } = options

  const [viewport, setViewport] = useState<GenomeViewport>(initialViewport)
  const debouncedViewport = useDebouncedViewport(viewport, debounceMs)

  const trackResults = tracks.map((track) => useGenomeTrack(track, debouncedViewport))

  const zoomIn = useCallback(() => {
    setViewport((current) => zoomViewport(current, 1 / ZOOM_FACTOR))
  }, [])

  const zoomOut = useCallback(() => {
    setViewport((current) => zoomViewport(current, ZOOM_FACTOR))
  }, [])

  const accel = useCallback((span: number, sign: 1 | -1) => {
    return sign * Math.max(1, Math.round(span * PAN_FRACTION))
  }, [])

  const panLeft = useCallback(() => {
    setViewport((current) => panViewport(current, accel(viewportBaseCount(current), -1)))
  }, [accel])

  const panRight = useCallback(() => {
    setViewport((current) => panViewport(current, accel(viewportBaseCount(current), 1)))
  }, [accel])

  const reset = useCallback(() => {
    setViewport({ ...initialViewport, bounds: initialViewport.bounds })
  }, [initialViewport])

  const navigateTo = useCallback((interval: GenomicInterval) => {
    setViewport((current) => ({
      chromosome: interval.chromosome,
      start: interval.start,
      end: interval.end,
      bounds: current.bounds,
    }))
  }, [])

  return { viewport, trackResults, zoomIn, zoomOut, panLeft, panRight, reset, navigateTo }
}
