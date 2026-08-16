'use client'

import { useId, useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import { formatBasePosition } from '@/lib/genome/geometry'
import { computeTicks } from '@/lib/genome/geometry'
import type { AxisTick } from '@/lib/genome/geometry'
import { createScale } from '@/lib/genome/geometry'
import type { CoverageBin } from '@/lib/scientific/advancedTypes'
import { coverageBinTooltip } from '@/lib/scientific/coverage'
import { coverageColumns } from '@/lib/scientific/downsample'
import {
  DEFAULT_CHART_HEIGHT,
  DEFAULT_CHART_MARGINS,
  GRIDLINE_TARGET,
  plotArea,
} from '@/lib/scientific/geometry'
import { createContinuousScale, formatTickValue } from '@/lib/scientific/scale'
import { formatTooltipValue } from '@/lib/scientific/tooltip'
import { useChartSize } from '@/lib/scientific/useChartSize'
import type { CoverageChartResult } from '@/lib/scientific/useCoverageChart'

import { ChartTooltip } from './ChartTooltip'

const AXIS_COLOR = '#cbd5e1'
const GRID_COLOR = '#e2e8f0'
const COVERAGE_COLOR = '#2563eb'
const CAPTION_COLOR = '#94a3b8'
const MAX_COVERAGE_COLUMNS = 2000

export interface CoverageChartProps {
  /** View model produced by `useCoverageChart`. */
  result: CoverageChartResult
  /** Container heading. */
  title?: string
  /** Optional fixed pixel width (defaults to measured container width). */
  width?: number
  /** Optional fixed pixel height (defaults to `DEFAULT_CHART_HEIGHT`). */
  height?: number
}

/**
 * Coverage Chart (Phase 6.8).
 *
 * Renders a `CoverageDataset` as an interactive SVG area chart of per-bin
 * read depth over a one-based inclusive genomic interval. The x-axis reuses
 * the Phase 6.2 genome coordinate utilities (`createScale`, `computeTicks`,
 * `formatBasePosition`) and the viewport navigation comes from
 * `lib/genome/viewport.ts`, so intervals, ticks, and zoom/pan are shared with
 * the Genome Browser rather than re-implemented. Bins expose hover tooltips
 * and keyboard-accessible selection with a readable detail panel. Consumes a
 * `CoverageChartResult` from `useCoverageChart`.
 */
export function CoverageChart({
  result,
  title = 'Coverage Chart',
  width,
  height = DEFAULT_CHART_HEIGHT,
}: CoverageChartProps) {
  const size = useChartSize(height)
  const chartWidth = width ?? size.width
  const margins = DEFAULT_CHART_MARGINS
  const plot = useMemo(() => plotArea(chartWidth, height, margins), [chartWidth, height, margins])
  const [hoveredBin, setHoveredBin] = useState<CoverageBin | null>(null)
  const [hoveredPosition, setHoveredPosition] = useState<{ x: number; y: number } | null>(null)

  const dataset = result.dataset
  const viewport = result.viewport
  const description = dataset
    ? dataset.metadata?.description !== undefined
      ? String(dataset.metadata.description)
      : `${result.chromosome !== '' ? result.chromosome : 'no chromosome'} coverage`
    : undefined

  const domain = result.domain
  const yScale = useMemo(
    () =>
      domain === undefined
        ? createContinuousScale([0, 1], [plot.y0 + plot.height, plot.y0])
        : createContinuousScale(
            [Math.max(0, domain.min), Math.max(1, domain.max)],
            [plot.y0 + plot.height, plot.y0],
          ),
    [domain, plot],
  )
  const yTicks = useMemo(() => yScale.ticks(GRIDLINE_TARGET), [yScale])

  return (
    <VisualizationContainer
      title={title}
      description={description}
      status={result.status}
      error={result.error}
      loadingLabel="Loading coverage data..."
      emptyMessage="No coverage data to show."
      errorTitle="Failed to load coverage data"
      onRetry={result.refetch}
    >
      {result.status === 'success' && dataset ? (
        <div className="flex w-full flex-col gap-2">
          <div className="flex w-full flex-wrap items-center justify-between gap-2">
            <output className="text-xs text-gray-500" aria-live="polite">
              {result.chromosome !== '' ? result.chromosome : 'no chromosome'} ·{' '}
              {dataset.bins.length} bins
            </output>
            <CoverageControls result={result} />
          </div>
          <div
            ref={size.ref}
            className="relative w-full"
            onMouseLeave={() => {
              setHoveredBin(null)
              setHoveredPosition(null)
            }}
          >
            <svg
              width={chartWidth}
              height={height}
              viewBox={`0 0 ${chartWidth} ${height}`}
              preserveAspectRatio="xMidYMid meet"
              // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps
              // the interactive bin controls inside the accessibility tree (see NetworkViewer).
              role="group"
              aria-label={`${dataset.title} coverage chart: ${dataset.bins.length} bins on ${result.chromosome}`}
              data-testid="coverage-svg"
              className="block w-full rounded-md border border-gray-200 bg-white"
            >
              <CoverageGridLines plot={plot} yScale={yScale} yTicks={yTicks} />
              {viewport !== undefined ? (
                <CoverageBins
                  dataset={dataset}
                  chromosome={result.chromosome}
                  viewport={viewport}
                  plot={plot}
                  yScale={yScale}
                  onHover={(bin, position) => {
                    setHoveredBin(bin)
                    setHoveredPosition(position)
                  }}
                  onHoverOut={() => {
                    setHoveredBin(null)
                    setHoveredPosition(null)
                  }}
                />
              ) : null}
              {viewport !== undefined ? (
                <CoverageAxes
                  chromosome={result.chromosome}
                  viewport={viewport}
                  plot={plot}
                  yScale={yScale}
                  yTicks={yTicks}
                />
              ) : null}
            </svg>
            {hoveredBin !== null && hoveredPosition !== null ? (
              <ChartTooltip
                tooltip={coverageBinTooltip(hoveredBin)}
                x={hoveredPosition.x}
                y={hoveredPosition.y}
                width={chartWidth}
              />
            ) : null}
          </div>
          <CoverageDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}

function CoverageControls({ result }: { result: CoverageChartResult }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <fieldset aria-label="Chromosome" className="flex items-center gap-1 border-0 p-0">
        {result.chromosomes.map((chromosome) => (
          <button
            key={chromosome}
            type="button"
            aria-pressed={result.chromosome === chromosome}
            onClick={() => result.selectChromosome(chromosome)}
            className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
          >
            {chromosome}
          </button>
        ))}
      </fieldset>
      <fieldset aria-label="Viewport navigation" className="flex items-center gap-1 border-0 p-0">
        <button
          type="button"
          onClick={() => result.zoom(0.5)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Zoom in
        </button>
        <button
          type="button"
          onClick={() => result.zoom(2)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Zoom out
        </button>
        <button
          type="button"
          onClick={() => {
            const span = result.viewport ? viewportSpan(result.viewport) : 0
            result.pan(-span / 2)
          }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Pan left
        </button>
        <button
          type="button"
          onClick={() => {
            const span = result.viewport ? viewportSpan(result.viewport) : 0
            result.pan(span / 2)
          }}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Pan right
        </button>
        <button
          type="button"
          onClick={result.resetViewport}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          Reset
        </button>
      </fieldset>
    </div>
  )
}

function viewportSpan(viewport: { start: number; end: number }): number {
  return Math.max(1, viewport.end - viewport.start + 1)
}

function CoverageGridLines({
  plot,
  yScale,
  yTicks,
}: {
  plot: ReturnType<typeof plotArea>
  yScale: ReturnType<typeof createContinuousScale>
  yTicks: number[]
}) {
  return (
    <g data-testid="coverage-grid">
      {yTicks.map((tick) => {
        const y = yScale.toPixel(tick)
        return (
          <line
            key={tick}
            x1={plot.x0}
            y1={y}
            x2={plot.x0 + plot.width}
            y2={y}
            stroke={GRID_COLOR}
            strokeWidth={1}
          />
        )
      })}
    </g>
  )
}

function CoverageBins({
  dataset,
  chromosome,
  viewport,
  plot,
  yScale,
  onHover,
  onHoverOut,
}: {
  dataset: CoverageChartResult['dataset']
  chromosome: string
  viewport: { start: number; end: number; bounds?: { length: number } }
  plot: ReturnType<typeof plotArea>
  yScale: ReturnType<typeof createContinuousScale>
  onHover: (bin: CoverageBin, position: { x: number; y: number }) => void
  onHoverOut: () => void
}) {
  const scale = useMemo(
    () => createScale(viewport.start, viewport.end, plot.width),
    [viewport, plot],
  )
  const bins = useMemo(
    () =>
      dataset === undefined ? [] : dataset.bins.filter((bin) => bin.chromosome === chromosome),
    [dataset, chromosome],
  )
  // When a chromosome has far more bins than pixels, aggregate to per-pixel
  // peak-preserving columns so both the path and the interactive targets stay
  // bounded (see docs/visualization/performance.md). Under the cap, bins are
  // rendered exactly as provided.
  const columns = useMemo(
    () => coverageColumns(bins, (base) => scale.toX(base), plot.width, MAX_COVERAGE_COLUMNS),
    [bins, scale, plot.width],
  )
  const points = useMemo(
    () =>
      columns.map((bin) => {
        const x0 = scale.toX(bin.start)
        const x1 = scale.toX(bin.end + 1)
        return { bin, x0, x1, y: yScale.toPixel(bin.coverage) }
      }),
    [columns, scale, yScale],
  )

  if (dataset === undefined || chromosome === '') return null

  const areaPath = buildAreaPath(plot, points)
  const linePath = buildLinePath(points)

  return (
    <g data-testid="coverage-bins">
      <path d={areaPath} fill={COVERAGE_COLOR} opacity={0.25} data-testid="coverage-area" />
      <path
        d={linePath}
        fill="none"
        stroke={COVERAGE_COLOR}
        strokeWidth={1.5}
        data-testid="coverage-line"
      />
      {points.map(({ bin, x0, x1 }) => {
        const width = Math.max(1, x1 - x0)
        const position = { x: x0 + width / 2, y: yScale.toPixel(bin.coverage) }
        return (
          <rect
            key={`${bin.chromosome}-${bin.start}-${bin.end}`}
            data-testid={`bin-${bin.start}-${bin.end}`}
            x={x0}
            y={plot.y0}
            width={width}
            height={plot.height}
            fill="transparent"
            stroke="none"
            role="button"
            aria-label={`Select ${coverageBinTooltip(bin).title} ${formatBasePosition(bin.start)}–${formatBasePosition(bin.end)}`}
            tabIndex={0}
            onMouseEnter={() => onHover(bin, position)}
            onMouseLeave={onHoverOut}
            onFocus={() => onHover(bin, position)}
            onBlur={onHoverOut}
          />
        )
      })}
    </g>
  )
}

function buildAreaPath(
  plot: ReturnType<typeof plotArea>,
  points: Array<{ x0: number; x1: number; y: number }>,
): string {
  if (points.length === 0) return ''
  const base = plot.y0 + plot.height
  const segments = points.map((point, index) => {
    const first = index === 0 ? `M ${point.x0} ${base}` : ''
    return `${first} L ${point.x0} ${point.y} L ${point.x1} ${point.y}`
  })
  const last = points[points.length - 1]
  return `${segments.join(' ')} L ${last.x1} ${base} Z`
}

function buildLinePath(points: Array<{ x0: number; x1: number; y: number }>): string {
  if (points.length === 0) return ''
  const segments = points.map((point, index) => {
    const first = index === 0 ? `M ${point.x0} ${point.y}` : ''
    return `${first} L ${point.x1} ${point.y}`
  })
  return segments.join(' ')
}

function CoverageDetail({ result }: { result: CoverageChartResult }) {
  const dataset = result.dataset
  const headingId = useId()
  if (dataset === undefined) return null
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby={headingId}
      data-testid="coverage-selection-detail"
    >
      <h3 id={headingId} className="text-sm font-semibold text-gray-900">
        {result.chromosome !== '' ? result.chromosome : 'Coverage'}
      </h3>
      <p className="text-xs text-gray-500">
        {dataset.bins.length} bins ·{' '}
        {result.viewport !== undefined
          ? `${formatBasePosition(result.viewport.start)}–${formatBasePosition(result.viewport.end)}`
          : 'viewport not available'}
      </p>
      <dl className="grid w-full grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
        {result.domain !== undefined ? (
          <div className="flex gap-2 text-sm">
            <dt className="text-gray-500">Coverage range</dt>
            <dd className="text-gray-900">
              {formatTooltipValue(result.domain.min)} – {formatTooltipValue(result.domain.max)}
            </dd>
          </div>
        ) : null}
        {dataset.metadata !== undefined
          ? Object.entries(dataset.metadata).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-sm">
                <dt className="text-gray-500">{key}</dt>
                <dd className="text-gray-900">{String(value)}</dd>
              </div>
            ))
          : null}
      </dl>
    </section>
  )
}

function CoverageAxes({
  chromosome,
  viewport,
  plot,
  yScale,
  yTicks,
}: {
  chromosome: string
  viewport: { start: number; end: number; bounds?: { length: number } }
  plot: ReturnType<typeof plotArea>
  yScale: ReturnType<typeof createContinuousScale>
  yTicks: number[]
}) {
  const scale = useMemo(
    () => createScale(viewport.start, viewport.end, plot.width),
    [viewport, plot],
  )
  const ticks = useMemo(() => computeTicks(viewport.start, viewport.end, 8, 4), [viewport])
  const baselineY = plot.y0 + plot.height
  return (
    <g data-testid="coverage-axes">
      <g data-testid="coverage-y-ticks">
        {yTicks.map((tick) => (
          <text
            key={tick}
            x={plot.x0 - 8}
            y={yScale.toPixel(tick)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={11}
            fill="#475569"
          >
            {formatTickValue(tick)}
          </text>
        ))}
      </g>
      <text
        x={8}
        y={plot.y0 + plot.height / 2}
        transform={`rotate(-90 8 ${plot.y0 + plot.height / 2})`}
        textAnchor="middle"
        fontSize={12}
        fill={CAPTION_COLOR}
        data-testid="coverage-y-label"
      >
        Coverage
      </text>
      <g data-testid="coverage-x-ticks">
        {ticks.map((tick) =>
          tick.major ? (
            <text
              key={tick.position}
              x={plot.x0 + scale.toX(tick.position)}
              y={baselineY + 14}
              textAnchor="middle"
              fontSize={11}
              fill="#475569"
            >
              {tick.label}
            </text>
          ) : (
            <line
              key={`minor-${tick.position}`}
              x1={plot.x0 + scale.toX(tick.position)}
              y1={baselineY}
              x2={plot.x0 + scale.toX(tick.position)}
              y2={baselineY + 4}
              stroke={AXIS_COLOR}
              strokeWidth={1}
            />
          ),
        )}
      </g>
      <text
        x={plot.x0 + plot.width / 2}
        y={baselineY + 18}
        textAnchor="middle"
        fontSize={12}
        fill={CAPTION_COLOR}
        data-testid="coverage-x-label"
      >
        {chromosome}
      </text>
      <line
        x1={plot.x0}
        y1={baselineY}
        x2={plot.x0 + plot.width}
        y2={baselineY}
        stroke={AXIS_COLOR}
        strokeWidth={1}
      />
      <line
        x1={plot.x0}
        y1={plot.y0}
        x2={plot.x0}
        y2={baselineY}
        stroke={AXIS_COLOR}
        strokeWidth={1}
      />
    </g>
  )
}
