'use client'

import { type FormEvent, useCallback, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import {
  type AxisTick,
  computeTicks,
  createScale,
  formatBasePosition,
  formatRegionLabel,
} from '@/lib/genome/geometry'
import { type RegionValidationError, parseGenomeRegion } from '@/lib/genome/region'
import { featuresInViewport } from '@/lib/genome/tracks'
import type { GenomeViewport, GenomicFeature } from '@/lib/genome/types'
import {
  type GenomeBrowserOptions,
  type GenomeBrowserResult,
  type GenomeTrackData,
  type GenomeTrackDefinition,
  useGenomeBrowser,
  useGenomeTrack,
} from '@/lib/genome/useGenomeBrowser'
import { viewportBaseCount } from '@/lib/genome/viewport'

import { VariantTrack } from './VariantTrack'

const SVG_WIDTH = 1000
const AXIS_HEIGHT = 28
const TRACK_HEADER_WIDTH = 96
const ROW_HEIGHT = 16

/**
 * Draws the base-position axis for the visible viewport.
 *
 * Shares `SVG_WIDTH` and `TRACK_HEADER_WIDTH` with the track lanes so tick
 * positions align with feature positions. Rendered with `w-full`, the same
 * as track lanes, so the alignment survives container resizing.
 */
function AxisSvg({ viewport }: { viewport: GenomeViewport }) {
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - TRACK_HEADER_WIDTH)
  const ticks = computeTicks(viewport.start, viewport.end, 8)

  return (
    <svg
      viewBox={`0 0 ${SVG_WIDTH} ${AXIS_HEIGHT}`}
      className="w-full"
      aria-hidden="true"
      data-testid="axis-region"
      data-viewport={formatRegionLabel(viewport.chromosome, viewport.start, viewport.end)}
    >
      {ticks.map((tick: AxisTick, index) => {
        const x = TRACK_HEADER_WIDTH + scale.toX(tick.position)
        return (
          <g key={`${tick.position}-${index}`}>
            <line x1={x} y1={AXIS_HEIGHT - 12} x2={x} y2={AXIS_HEIGHT - 4} stroke="#cbd5e1" />
            {tick.major ? (
              <text x={x} y={AXIS_HEIGHT - 16} fontSize={11} fill="#64748b" textAnchor="middle">
                {formatBasePosition(tick.position)}
              </text>
            ) : null}
          </g>
        )
      })}
    </svg>
  )
}

/**
 * Draws one lane of span features (genes/transcripts).
 *
 * Features are clipped to the viewport before their pixel geometry is
 * computed so glyphs never spill into the reserved header column. Point
 * variants are rendered by the reusable `VariantTrack` component instead.
 */
function GenomeTrackSvg({
  viewport,
  features,
}: {
  viewport: GenomeViewport
  features: readonly GenomicFeature[]
}) {
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - TRACK_HEADER_WIDTH)

  return (
    <g>
      {features.map((feature, index) => {
        // Clip to the visible window (one-based inclusive).
        const clipStart = Math.max(feature.start, viewport.start)
        const clipEnd = Math.min(feature.end, viewport.end)
        const x = TRACK_HEADER_WIDTH + scale.toX(clipStart)
        const width = Math.max(3, scale.spanToPixels(clipEnd - clipStart + 1))
        const forward = feature.strand !== '-'
        const fill = forward ? '#2563eb' : '#7c3aed'
        const height = ROW_HEIGHT - 4
        const y = 2
        const arrowLength = Math.min(8, width / 2)
        const bodyWidth = Math.max(1, width - arrowLength)
        // Arrowhead sits at the feature start for reverse strand, at the end
        // for forward strand, always outside the body rectangle.
        const arrow = forward
          ? `M ${x + bodyWidth} ${y} l ${arrowLength} ${height / 2} l ${-arrowLength} ${height / 2} Z`
          : `M ${x} ${y} l ${arrowLength} ${height / 2} l ${-arrowLength} ${height / 2} Z`
        return (
          <g key={`${feature.id}-${index}`}>
            <rect
              x={forward ? x : x + arrowLength}
              y={y}
              width={bodyWidth}
              height={height}
              fill={fill}
              rx={1}
            />
            <path d={arrow} fill={fill} />
            <title>{feature.name ?? feature.id}</title>
          </g>
        )
      })}
    </g>
  )
}

function BrowserControls({ browser }: { browser: GenomeBrowserResult }) {
  const [regionText, setRegionText] = useState('')
  const [regionError, setRegionError] = useState<RegionValidationError | null>(null)

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const result = parseGenomeRegion(regionText)
      if (result.ok) {
        browser.navigateTo(result.interval)
        setRegionText('')
        setRegionError(null)
      } else {
        setRegionError(result.error)
      }
    },
    [browser, regionText],
  )

  const controls = [
    { label: 'Zoom in', action: browser.zoomIn, glyph: '+' },
    { label: 'Zoom out', action: browser.zoomOut, glyph: '\u2212' },
    { label: 'Scroll left', action: browser.panLeft, glyph: '\u2190' },
    { label: 'Scroll right', action: browser.panRight, glyph: '\u2192' },
    { label: 'Reset view', action: browser.reset, glyph: '\u21BA' },
  ]

  return (
    <div className="flex w-full flex-wrap items-center gap-2">
      <fieldset className="flex items-center gap-1 border-0 p-0" aria-label="Viewport navigation">
        <legend className="sr-only">Viewport navigation</legend>
        {controls.map((control) => (
          <button
            key={control.label}
            type="button"
            onClick={control.action}
            aria-label={control.label}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
          >
            {control.glyph}
          </button>
        ))}
      </fieldset>
      <form
        className="ml-auto flex items-center gap-2"
        onSubmit={handleSubmit}
        aria-label="Go to region"
        noValidate
      >
        <label htmlFor="genome-region-input" className="text-sm text-gray-600">
          Region
        </label>
        <input
          id="genome-region-input"
          type="text"
          value={regionText}
          onChange={(event) => {
            setRegionText(event.target.value)
            setRegionError(null)
          }}
          placeholder="chr1:100000-200000"
          aria-invalid={regionError !== null}
          aria-describedby={regionError ? 'genome-region-error' : undefined}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        />
        <button
          type="submit"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
        >
          Go
        </button>
      </form>
      {regionError ? (
        <span id="genome-region-error" role="alert" className="w-full text-sm text-red-600">
          {regionError.message}
        </span>
      ) : null}
    </div>
  )
}

function BrowserStatus({ viewport }: { viewport: GenomeViewport }) {
  const bases = viewportBaseCount(viewport)
  return (
    <output className="text-xs text-gray-500" aria-live="polite">
      {formatRegionLabel(viewport.chromosome, viewport.start, viewport.end)} &middot;{' '}
      {bases.toLocaleString('en-US')} bp
    </output>
  )
}

/**
 * Renders one track lane as its own stable component instance.
 *
 * Being a component (not a loop inside a hook) keeps the Rules of Hooks
 * satisfied as the track set grows, shrinks, or reorders. Span tracks
 * (genes/transcripts) render arrow glyphs; point variants render through the
 * reusable `VariantTrack` component.
 */
function BrowserTrack({
  track,
  debouncedViewport,
}: {
  track: GenomeTrackDefinition
  debouncedViewport: GenomeViewport
}) {
  if (track.kind === 'variants') {
    return <VariantTrack track={track} debouncedViewport={debouncedViewport} />
  }

  const data = useGenomeTrack(track, debouncedViewport)
  const viewport = debouncedViewport
  const features = featuresInViewport(data.data ?? [], viewport)

  return (
    <VisualizationContainer
      title={data.label}
      status={data.status}
      error={data.errorMessage ? { message: data.errorMessage } : undefined}
      loadingLabel={`Loading ${data.label.toLowerCase()}...`}
      emptyMessage={`No ${data.label.toLowerCase()} found in region.`}
      onRetry={data.refetch}
    >
      <svg viewBox={`0 0 ${SVG_WIDTH} ${ROW_HEIGHT}`} className="w-full" aria-hidden="true">
        {data.status === 'success' ? (
          <GenomeTrackSvg viewport={viewport} features={features} />
        ) : null}
      </svg>
    </VisualizationContainer>
  )
}

export interface GenomeBrowserProps extends GenomeBrowserOptions {
  /** Tracks to fetch and render, in display order. */
  tracks: GenomeTrackDefinition[]
}

/**
 * Genome Browser (Phase 6.2).
 *
 * An interactive, accessible viewport over a chromosome. Parent components
 * supply an `initialViewport` (a 1-based inclusive region) and track
 * definitions; each track is its own async request scoped to the visible
 * region, flowing through the Phase 6.1 state layer (`useVisualizationData`).
 */
export function GenomeBrowser({ initialViewport, tracks, debounceMs }: GenomeBrowserProps) {
  const browser = useGenomeBrowser({ initialViewport, debounceMs })

  return (
    <div className="flex w-full flex-col gap-4">
      <BrowserControls browser={browser} />
      <BrowserStatus viewport={browser.viewport} />
      <div className="w-full rounded-lg border border-gray-200 bg-white p-4 sm:p-6">
        <AxisSvg viewport={browser.debouncedViewport} />
      </div>
      <div className="flex w-full flex-col gap-4">
        {tracks.map((track) => (
          <BrowserTrack
            key={track.id}
            track={track}
            debouncedViewport={browser.debouncedViewport}
          />
        ))}
      </div>
    </div>
  )
}

// Keep the GenomeTrackData type referenced so it stays part of the public
// surface for consumers that render custom track UI.
export type { GenomeTrackData }
