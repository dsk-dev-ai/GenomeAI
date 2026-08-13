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
 *
 * ## Rules of Hooks
 *
 * `useGenomeBrowser` owns the viewport and navigation only. Per-track data
 * loading lives in `useGenomeTrack`, which callers must invoke from a
 * stable component instance (one per track), not from `Array.prototype.map`
 * inside a hook — keeping hook order deterministic as track sets change.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import type { VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

import type { TrackKind } from './tracks'
import type { GenomeViewport, GenomicFeature, GenomicInterval, VariantFeature } from './types'
import { PAN_FRACTION, ZOOM_FACTOR, panViewport, viewportBaseCount, zoomViewport } from './viewport'

/** Loads a track's visible features for a one-based inclusive interval. */
export type GenomeTrackLoader<T extends GenomicFeature = GenomicFeature> = (
  interval: GenomicInterval,
  signal: AbortSignal,
) => Promise<T[]>

/** Definition of a span track lane (genes, transcripts, ...). */
export interface SpanTrackDefinition {
  id: string
  label: string
  kind: Exclude<TrackKind, 'variants'>
  loader: GenomeTrackLoader<GenomicFeature>
}

/** Definition of a point-variant track lane. */
export interface VariantTrackDefinition {
  id: string
  label: string
  kind: 'variants'
  loader: GenomeTrackLoader<VariantFeature>
}

/**
 * Definition of a visible track; discriminated on `kind` so each lane
 * receives the exact feature type its loader resolves to.
 */
export type GenomeTrackDefinition = SpanTrackDefinition | VariantTrackDefinition

/** A track's data-layer result, keyed by `id`. */
export interface GenomeTrackDataBase<T extends GenomicFeature> {
  id: string
  label: string
  kind: TrackKind
  loader: GenomeTrackLoader<T>
  status: VisualizationStatus
  data: T[] | undefined
  /** Present when `status === 'error'`. */
  errorMessage: string | undefined
  /** Re-runs the track's request (used by the retry UI). */
  refetch: () => void
}

export type GenomeTrackData<T extends GenomeTrackDefinition = GenomeTrackDefinition> =
  T extends VariantTrackDefinition
    ? GenomeTrackDataBase<VariantFeature> & { kind: 'variants' }
    : GenomeTrackDataBase<GenomicFeature> & { kind: Exclude<TrackKind, 'variants'> }

export interface GenomeBrowserOptions {
  /** Viewport shown on first render. */
  initialViewport: GenomeViewport
  /** Debounce (ms) applied to viewport changes before refetching. */
  debounceMs?: number
}

export interface GenomeBrowserResult {
  /** Current, immutable viewport. */
  viewport: GenomeViewport
  /**
   * Viewport that has settled past the debounce window. Track loaders fetch
   * only this settled region, so rapid pan/zoom does not fire per-frame
   * requests.
   */
  debouncedViewport: GenomeViewport
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

/**
 * Drives one track's async lifecycle for the settled viewport.
 *
 * Must be called from a stable component instance (one per track). Refetches
 * when the debounced viewport settles on a new region; the initial request
 * is fired by `useVisualizationData`.
 */
export function useGenomeTrack<T extends GenomeTrackDefinition>(
  definition: T,
  debouncedViewport: GenomeViewport,
): GenomeTrackData<T> {
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

  // `data` is narrowed to the definition's exact feature type by the
  // `GenomeTrackData` mapped type; the hook is the single adapter boundary
  // where the shared `GenomicFeature` result becomes the lane's typed data.
  return {
    id: definition.id,
    label: definition.label,
    kind: definition.kind,
    loader: definition.loader,
    status,
    data,
    errorMessage: error?.message,
    refetch,
  } as GenomeTrackData<T>
}

/** Clamps an interval to contig bounds (inclusive 1..length). */
function clampToBounds(interval: GenomicInterval, length: number): GenomicInterval {
  const start = Math.min(Math.max(interval.start, 1), length)
  const end = Math.min(Math.max(interval.end, start), length)
  return { chromosome: interval.chromosome, start, end }
}

export function useGenomeBrowser(options: GenomeBrowserOptions): GenomeBrowserResult {
  const { initialViewport, debounceMs = 300 } = options

  const [viewport, setViewport] = useState<GenomeViewport>(initialViewport)
  const debouncedViewport = useDebouncedViewport(viewport, debounceMs)

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
    setViewport({ ...initialViewport })
  }, [initialViewport])

  const navigateTo = useCallback((interval: GenomicInterval) => {
    setViewport((current) => {
      // Bounds describe the current contig; a different chromosome has
      // unknown extent, so never carry stale bounds across a chromosome
      // change (that would clamp against the wrong length).
      const sameContig = interval.chromosome === current.chromosome
      const bounds = sameContig ? current.bounds : undefined
      const clamped = bounds ? clampToBounds(interval, bounds.length) : interval
      return { ...clamped, bounds }
    })
  }, [])

  return { viewport, debouncedViewport, zoomIn, zoomOut, panLeft, panRight, reset, navigateTo }
}
