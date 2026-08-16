'use client'

import { useId, useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import type { VolcanoDataset, VolcanoPoint } from '@/lib/scientific/advancedTypes'
import {
  DEFAULT_CHART_HEIGHT,
  DEFAULT_CHART_MARGINS,
  GRIDLINE_TARGET,
  plotArea,
} from '@/lib/scientific/geometry'
import { createContinuousScale, formatTickValue } from '@/lib/scientific/scale'
import { formatTooltipValue } from '@/lib/scientific/tooltip'
import { useChartSize } from '@/lib/scientific/useChartSize'
import type { VolcanoPlotResult } from '@/lib/scientific/useVolcanoPlot'
import { isVolcanoHighlighted, volcanoPointTooltip } from '@/lib/scientific/volcano'

import { ChartAxes } from './ChartAxes'
import { ChartTooltip } from './ChartTooltip'

const POINT_RADIUS = 4
const HIT_RADIUS = 11
const HIGHLIGHT_COLOR = '#dc2626'
const BASE_COLOR = '#94a3b8'
const THRESHOLD_COLOR = '#94a3b8'

export interface VolcanoPlotProps {
  /** View model produced by `useVolcanoPlot`. */
  result: VolcanoPlotResult
  /** Container heading. */
  title?: string
  /** Optional fixed pixel width (defaults to measured container width). */
  width?: number
  /** Optional fixed pixel height (defaults to `DEFAULT_CHART_HEIGHT`). */
  height?: number
}

/**
 * Volcano Plot (Phase 6.8).
 *
 * Renders a `VolcanoDataset` as an interactive SVG scatter plot: effect size
 * on the x-axis, significance on the y-axis, and points colored by whether
 * they pass the user-supplied highlight thresholds. Threshold lines (dashed)
 * mark the callout region. Points expose hover tooltips and keyboard-
 * accessible selection with a readable detail panel. Consumes a
 * `VolcanoPlotResult` from `useVolcanoPlot`; all data transformation stays in
 * `lib/scientific`.
 */
export function VolcanoPlot({
  result,
  title = 'Volcano Plot',
  width,
  height = DEFAULT_CHART_HEIGHT,
}: VolcanoPlotProps) {
  const size = useChartSize(height)
  const chartWidth = width ?? size.width
  const margins = DEFAULT_CHART_MARGINS
  const plot = useMemo(() => plotArea(chartWidth, height, margins), [chartWidth, height, margins])
  const [hoveredKey, setHoveredKey] = useState<string | null>(null)
  const [hoveredPosition, setHoveredPosition] = useState<{ x: number; y: number } | null>(null)

  const dataset = result.dataset
  const domains = result.domains
  const description = dataset
    ? dataset.metadata?.description !== undefined
      ? String(dataset.metadata.description)
      : `${dataset.points.length} features tested`
    : undefined

  const xScale = useMemo(
    () =>
      domains === undefined
        ? createContinuousScale([-1, 1], [plot.x0, plot.x0 + plot.width])
        : createContinuousScale(
            [domains.effectSize.min, domains.effectSize.max],
            [plot.x0, plot.x0 + plot.width],
          ),
    [domains, plot],
  )

  const yScale = useMemo(
    () =>
      domains === undefined
        ? createContinuousScale([0, 1], [plot.y0 + plot.height, plot.y0])
        : createContinuousScale(
            [domains.significance.min, domains.significance.max],
            [plot.y0 + plot.height, plot.y0],
          ),
    [domains, plot],
  )

  const yTicks = useMemo(() => yScale.ticks(GRIDLINE_TARGET), [yScale])
  const xTicks = useMemo(() => xScale.ticks(GRIDLINE_TARGET), [xScale])

  const hovered = useMemo(() => {
    if (dataset === undefined || hoveredKey === null) return null
    const point = dataset.points.find((candidate) => candidate.identifier === hoveredKey)
    if (point === undefined) return null
    return {
      tooltip: volcanoPointTooltip(point),
      x: xScale.toPixel(point.effectSize),
      y: yScale.toPixel(point.significance),
    }
  }, [dataset, hoveredKey, xScale, yScale])

  return (
    <VisualizationContainer
      title={title}
      description={description}
      status={result.status}
      error={result.error}
      loadingLabel="Loading volcano data..."
      emptyMessage="No volcano data to show."
      errorTitle="Failed to load volcano data"
      onRetry={result.refetch}
    >
      {result.status === 'success' && dataset ? (
        <div className="flex w-full flex-col gap-2">
          <output className="text-xs text-gray-500" aria-live="polite">
            {dataset.points.length} features tested · {highlightCount(dataset, result.thresholds)}{' '}
            significant at the current thresholds
          </output>
          <div
            ref={size.ref}
            className="relative w-full"
            onMouseLeave={() => {
              setHoveredKey(null)
              setHoveredPosition(null)
            }}
          >
            <svg
              width={chartWidth}
              height={height}
              viewBox={`0 0 ${chartWidth} ${height}`}
              preserveAspectRatio="xMidYMid meet"
              // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps
              // the interactive point controls inside the accessibility tree (see NetworkViewer).
              role="group"
              aria-label={`${dataset.title} volcano plot: ${dataset.points.length} features`}
              data-testid="volcano-svg"
              className="block w-full rounded-md border border-gray-200 bg-white"
            >
              <ChartAxes
                plot={plot}
                xContinuousScale={xScale}
                xTicks={xTicks}
                yScale={yScale}
                yTicks={yTicks}
                xLabel="Effect size"
                yLabel="Significance"
                formatValue={formatTickValue}
              />
              <ThresholdLines plot={plot} xScale={xScale} yScale={yScale} result={result} />
              <g data-testid="volcano-points">
                {dataset.points.map((point) => {
                  const highlighted = isVolcanoHighlighted(point, result.thresholds)
                  const key = point.identifier
                  const selected = result.selectedKey === key
                  const label = `${point.identifier}: effect ${formatTooltipValue(point.effectSize)}, significance ${formatTooltipValue(point.significance)}`
                  return (
                    <VolcanoPointMark
                      key={key}
                      x={xScale.toPixel(point.effectSize)}
                      y={yScale.toPixel(point.significance)}
                      color={highlighted ? HIGHLIGHT_COLOR : BASE_COLOR}
                      label={label}
                      selected={selected}
                      testId={`point-${key}`}
                      onMouseEnter={() => {
                        setHoveredKey(key)
                        setHoveredPosition({
                          x: xScale.toPixel(point.effectSize),
                          y: yScale.toPixel(point.significance),
                        })
                      }}
                      onMouseLeave={() => setHoveredKey(null)}
                      onSelect={() => result.selectPoint(selected ? null : key)}
                    />
                  )
                })}
              </g>
            </svg>
            {hovered !== null && hoveredPosition !== null ? (
              <ChartTooltip
                tooltip={hovered.tooltip}
                x={hoveredPosition.x}
                y={hoveredPosition.y}
                width={chartWidth}
              />
            ) : null}
          </div>
          <VolcanoDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}

function highlightCount(
  dataset: VolcanoDataset,
  thresholds: VolcanoPlotResult['thresholds'],
): number {
  return dataset.points.filter((point) => isVolcanoHighlighted(point, thresholds)).length
}

function ThresholdLines({
  plot,
  xScale,
  yScale,
  result,
}: {
  plot: ReturnType<typeof plotArea>
  xScale: ReturnType<typeof createContinuousScale>
  yScale: ReturnType<typeof createContinuousScale>
  result: VolcanoPlotResult
}) {
  const { effectThreshold, significanceThreshold } = result.thresholds
  return (
    <g
      data-testid="volcano-thresholds"
      stroke={THRESHOLD_COLOR}
      strokeWidth={1}
      strokeDasharray="4 4"
      fill="none"
    >
      {effectThreshold !== undefined && effectThreshold > 0 ? (
        <>
          <line
            x1={xScale.toPixel(-effectThreshold)}
            y1={plot.y0}
            x2={xScale.toPixel(-effectThreshold)}
            y2={plot.y0 + plot.height}
          />
          <line
            x1={xScale.toPixel(effectThreshold)}
            y1={plot.y0}
            x2={xScale.toPixel(effectThreshold)}
            y2={plot.y0 + plot.height}
          />
        </>
      ) : null}
      {significanceThreshold !== undefined && significanceThreshold > 0 ? (
        <line
          x1={plot.x0}
          y1={yScale.toPixel(significanceThreshold)}
          x2={plot.x0 + plot.width}
          y2={yScale.toPixel(significanceThreshold)}
        />
      ) : null}
    </g>
  )
}

function VolcanoPointMark({
  x,
  y,
  color,
  label,
  selected,
  testId,
  onMouseEnter,
  onMouseLeave,
  onSelect,
}: {
  x: number
  y: number
  color: string
  label: string
  selected: boolean
  testId: string
  onMouseEnter: () => void
  onMouseLeave: () => void
  onSelect: () => void
}) {
  const [focused, setFocused] = useState(false)
  return (
    <g data-testid={testId} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
      <title>{label}</title>
      <circle cx={x} cy={y} r={selected ? POINT_RADIUS + 1 : POINT_RADIUS} fill={color} />
      {focused ? (
        <circle
          cx={x}
          cy={y}
          r={HIT_RADIUS + 1}
          fill="none"
          stroke="#0f172a"
          strokeWidth={2}
          strokeDasharray="3 3"
          pointerEvents="none"
          data-testid={`${testId}-focus-ring`}
        />
      ) : null}
      <circle
        cx={x}
        cy={y}
        r={HIT_RADIUS}
        fill="transparent"
        stroke="none"
        role="button"
        aria-label={`Select ${label}`}
        aria-pressed={selected}
        tabIndex={0}
        data-testid={`${testId}-hit`}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            onSelect()
          }
        }}
        onClick={(event) => {
          event.stopPropagation()
          onSelect()
        }}
      />
    </g>
  )
}

function VolcanoDetail({ result }: { result: VolcanoPlotResult }) {
  const dataset = result.dataset
  const selectedKey = result.selectedKey
  const headingId = useId()
  if (dataset === undefined || selectedKey === null) return null
  const point = dataset.points.find((candidate) => candidate.identifier === selectedKey)
  if (point === undefined) return null
  const tooltip = volcanoPointTooltip(point)
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby={headingId}
      data-testid="volcano-selection-detail"
    >
      <h3 id={headingId} className="text-sm font-semibold text-gray-900">
        {tooltip.title}
      </h3>
      <p className="text-xs text-gray-500">{tooltip.subtitle}</p>
      <dl className="grid w-full grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
        {tooltip.rows.map((row, index) => (
          <div key={`${row.label}-${index}`} className="flex gap-2 text-sm">
            <dt className="text-gray-500">{row.label}</dt>
            <dd className="text-gray-900">{row.value}</dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        onClick={result.clearSelection}
        className="mt-2 w-fit rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
      >
        Clear selection
      </button>
    </section>
  )
}
