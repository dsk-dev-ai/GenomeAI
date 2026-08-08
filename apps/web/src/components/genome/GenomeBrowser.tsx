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
import { parseGenomeRegion } from '@/lib/genome/region'
import { featuresInViewport } from '@/lib/genome/tracks'
import type { TrackKind } from '@/lib/genome/tracks'
import type { GenomeViewport } from '@/lib/genome/types'
import {
  type GenomeBrowserOptions,
  type GenomeBrowserResult,
  useGenomeBrowser,
} from '@/lib/genome/useGenomeBrowser'
import { viewportBaseCount } from '@/lib/genome/viewport'

const SVG_WIDTH = 1000
const AXIS_HEIGHT = 28
const TRACK_HEADER_WIDTH = 96
const ROW_HEIGHT = 16
const TRACK_GAP = 10

/**
 * Draws the base-position axis for the visible viewport.
 */
function AxisSvg({ viewport }: { viewport: GenomeViewport }) {
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - TRACK_HEADER_WIDTH)
  const ticks = computeTicks(viewport.start, viewport.end, 8)

  return (
    <svg viewBox={`0 0 ${SVG_WIDTH} ${AXIS_HEIGHT}`} className="min-w-[640px]" aria-hidden="true">
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
 * Draws one lane of genomic features.
 *
 * `kind` selects the glyph: genes/transcripts are packed arrow-ish
 * rectangles (strand-aware colour), variants are point marks. Features are
 * clipped to the viewport before rendering.
 */
function GenomeTrackSvg({
  viewport,
  features,
  kind,
}: {
  viewport: GenomeViewport
  features: readonly import('@/lib/genome/types').GenomicFeature[]
  kind: TrackKind
}) {
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - TRACK_HEADER_WIDTH)

  if (kind === 'variants') {
    return (
      <g>
        {features.map((feature, index) => {
          const x = TRACK_HEADER_WIDTH + scale.toX(feature.start)
          const y = ROW_HEIGHT / 2
          return (
            <g key={`${feature.id}-${index}`}>
              <line x1={x} y1={y - 5} x2={x} y2={y + 5} stroke="#0891b2" strokeWidth={2} />
              <title>{feature.name ?? feature.id}</title>
            </g>
          )
        })}
      </g>
    )
  }

  return (
    <g>
      {features.map((feature, index) => {
        const x = TRACK_HEADER_WIDTH + scale.toX(feature.start)
        const width = Math.max(3, scale.spanToPixels(feature.end - feature.start + 1))
        const forward = feature.strand !== '-'
        const fill = forward ? '#2563eb' : '#7c3aed'
        const height = ROW_HEIGHT - 4
        const y = 2
        const arrowLength = Math.min(8, width / 2)
        const bodyWidth = Math.max(1, width - arrowLength)
        const arrow = forward
          ? `M ${x + bodyWidth} ${y} l ${arrowLength} ${height / 2} l ${-arrowLength} ${height / 2} Z`
          : `M ${x + bodyWidth} ${y} l ${-arrowLength} ${height / 2} l ${arrowLength} ${height / 2} Z`
        return (
          <g key={`${feature.id}-${index}`}>
            <rect x={x} y={y} width={bodyWidth} height={height} fill={fill} rx={1} />
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

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const result = parseGenomeRegion(regionText)
      if (result.ok) {
        browser.navigateTo(result.interval)
      }
      setRegionText('')
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
      >
        <label htmlFor="genome-region-input" className="text-sm text-gray-600">
          Region
        </label>
        <input
          id="genome-region-input"
          type="text"
          value={regionText}
          onChange={(event) => setRegionText(event.target.value)}
          placeholder="chr1:100000-200000"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        />
        <button
          type="submit"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
        >
          Go
        </button>
      </form>
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

function BrowserTrack({
  track,
  viewport,
}: {
  track: ReturnType<typeof useGenomeBrowser>['trackResults'][number]
  viewport: GenomeViewport
}) {
  const features = featuresInViewport(track.data ?? [], viewport)

  return (
    <VisualizationContainer
      title={track.label}
      status={track.status}
      error={track.errorMessage ? { message: track.errorMessage } : undefined}
      loadingLabel={`Loading ${track.label.toLowerCase()}...`}
      emptyMessage={`No ${track.label.toLowerCase()} found in region.`}
      onRetry={track.refetch}
    >
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${ROW_HEIGHT + TRACK_GAP}`}
        className="h-[40px] w-full"
        aria-hidden="true"
      >
        {track.status === 'success' ? (
          <GenomeTrackSvg viewport={viewport} features={features} kind={track.kind} />
        ) : null}
      </svg>
    </VisualizationContainer>
  )
}

/**
 * Genome Browser (Phase 6.2).
 *
 * An interactive, accessible viewport over a chromosome. Parent components
 * supply an `initialViewport` (a 1-based inclusive region) and track
 * definitions; each track is its own async request scoped to the visible
 * region, flowing through the Phase 6.1 state layer (`useVisualizationData`).
 */
export function GenomeBrowser({ initialViewport, tracks, debounceMs }: GenomeBrowserOptions) {
  const browser = useGenomeBrowser({ initialViewport, tracks, debounceMs })

  return (
    <div className="flex w-full flex-col gap-4">
      <BrowserControls browser={browser} />
      <BrowserStatus viewport={browser.viewport} />
      <AxisSvg viewport={browser.viewport} />
      <div className="flex w-full flex-col gap-4">
        {browser.trackResults.map((track) => (
          <BrowserTrack key={track.id} track={track} viewport={browser.viewport} />
        ))}
      </div>
    </div>
  )
}
