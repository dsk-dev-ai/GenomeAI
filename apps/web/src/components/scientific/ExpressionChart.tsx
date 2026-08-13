'use client'

import { useId, useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import {
  DEFAULT_CHART_HEIGHT,
  DEFAULT_CHART_MARGINS,
  GRIDLINE_TARGET,
  plotArea,
  seriesColor,
} from '@/lib/scientific/geometry'
import { createCategoryScale, createContinuousScale, formatTickValue } from '@/lib/scientific/scale'
import { formatTooltipValue, lookupPoint, pointTooltip } from '@/lib/scientific/tooltip'
import { parsePointKey, pointKeyToString } from '@/lib/scientific/types'
import type {
  ExpressionDataset,
  ExpressionPoint,
  ExpressionSeries,
  PointKey,
} from '@/lib/scientific/types'
import { useChartSize } from '@/lib/scientific/useChartSize'
import type { ExpressionChartResult } from '@/lib/scientific/useExpressionChart'

import { ChartAxes } from './ChartAxes'
import { ChartLegend } from './ChartLegend'
import { ChartTooltip } from './ChartTooltip'

const POINT_RADIUS = 4
const HIT_RADIUS = 11

function SeriesPoint({
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

function SeriesLines({
  dataset,
  xScale,
  yScale,
  valueField,
}: {
  dataset: ExpressionDataset
  xScale: ReturnType<typeof createCategoryScale>
  yScale: ReturnType<typeof createContinuousScale>
  valueField: 'value' | 'normalizedValue'
}) {
  return (
    <g data-testid="chart-series-lines">
      {dataset.series.map((series, seriesIndex) => {
        const color = seriesColor(seriesIndex)
        const positions = series.points
          .map((point) => {
            const value = point[valueField]
            if (value === undefined || !Number.isFinite(value)) return null
            return { x: xScale.toPixel(point.sample), y: yScale.toPixel(value) }
          })
          .filter((position): position is { x: number; y: number } => position !== null)
        if (positions.length < 2) return null
        const pointsAttribute = positions.map((position) => `${position.x},${position.y}`).join(' ')
        return (
          <polyline
            key={series.id}
            points={pointsAttribute}
            fill="none"
            stroke={color}
            strokeWidth={1.5}
            opacity={0.7}
            data-testid={`series-line-${series.id}`}
          />
        )
      })}
    </g>
  )
}

function ChartControls({ result }: { result: ExpressionChartResult }) {
  if (!result.hasNormalizedValues) return null
  return (
    <fieldset className="flex items-center gap-1 border-0 p-0" aria-label="Y-axis value field">
      <legend className="sr-only">Y-axis value field</legend>
      {(['value', 'normalizedValue'] as const).map((field) => (
        <button
          key={field}
          type="button"
          aria-pressed={result.valueField === field}
          onClick={() => result.setValueField(field)}
          className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
        >
          {field === 'value' ? 'Value' : 'Normalized'}
        </button>
      ))}
    </fieldset>
  )
}

function ChartDetail({ result }: { result: ExpressionChartResult }) {
  const dataset = result.dataset
  const selectedKey = result.selectedKey
  const headingId = useId()
  if (dataset === undefined || selectedKey === null) return null

  const key = parsePointKey(selectedKey)
  if (key === undefined) return null
  const lookup = lookupPoint(dataset, key)
  if (lookup === undefined) return null

  const tooltip = pointTooltip(lookup.series, lookup.point)
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby={headingId}
      data-testid="chart-selection-detail"
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

export interface ExpressionChartProps {
  /** View model produced by `useExpressionChart`. */
  result: ExpressionChartResult
  /** Container heading. */
  title?: string
  /** Optional fixed pixel width (defaults to measured container width). */
  width?: number
  /** Optional fixed pixel height (defaults to `DEFAULT_CHART_HEIGHT`). */
  height?: number
}

function keyFor(series: ExpressionSeries, point: ExpressionPoint): string {
  return pointKeyToString({ seriesId: series.id, pointId: point.identifier, sample: point.sample })
}

/**
 * Expression Chart (Phase 6.7).
 *
 * Renders an `ExpressionDataset` as an interactive SVG scatter/line chart:
 * samples on the x-axis, the active value field on the y-axis, one series
 * (gene) per color, gridlines, axes, a legend, hover tooltips, and
 * keyboard-accessible point selection with a readable detail panel. Consumes
 * an `ExpressionChartResult` from `useExpressionChart`; all data
 * transformation stays in `lib/scientific`.
 */
export function ExpressionChart({
  result,
  title = 'Expression Chart',
  width,
  height = DEFAULT_CHART_HEIGHT,
}: ExpressionChartProps) {
  const size = useChartSize(height)
  const chartWidth = width ?? size.width
  const margins = DEFAULT_CHART_MARGINS
  const plot = useMemo(() => plotArea(chartWidth, height, margins), [chartWidth, height, margins])
  const [hoveredKey, setHoveredKey] = useState<PointKey | null>(null)

  const dataset = result.dataset
  const field = result.valueField

  const xScale = useMemo(
    () => createCategoryScale(result.samples, [plot.x0, plot.x0 + plot.width]),
    [result.samples, plot],
  )

  const yScale = useMemo(
    () =>
      createContinuousScale(
        [result.valueDomain.min, result.valueDomain.max],
        [plot.y0 + plot.height, plot.y0],
      ),
    [result.valueDomain, plot],
  )

  const yTicks = useMemo(() => yScale.ticks(GRIDLINE_TARGET), [yScale])

  const hovered = useMemo(() => {
    if (dataset === undefined || hoveredKey === null) return null
    const lookup = lookupPoint(dataset, hoveredKey)
    if (lookup === undefined) return null
    const value = lookup.point[field]
    if (value === undefined || !Number.isFinite(value)) return null
    return {
      tooltip: pointTooltip(lookup.series, lookup.point),
      x: xScale.toPixel(lookup.point.sample),
      y: yScale.toPixel(value),
    }
  }, [dataset, hoveredKey, field, xScale, yScale])

  const description = dataset
    ? dataset.metadata?.description !== undefined
      ? String(dataset.metadata.description)
      : `${result.samples.length} samples · ${dataset.series.length} series`
    : undefined

  return (
    <VisualizationContainer
      title={title}
      description={description}
      status={result.status}
      error={result.error}
      loadingLabel="Loading expression data..."
      emptyMessage="No expression data to show."
      errorTitle="Failed to load expression data"
      onRetry={result.refetch}
    >
      {result.status === 'success' && dataset ? (
        <div className="flex w-full flex-col gap-2">
          <div className="flex w-full flex-wrap items-center justify-between gap-2">
            <output className="text-xs text-gray-500" aria-live="polite">
              {result.samples.length} samples · {dataset.series.length} series
            </output>
            <ChartControls result={result} />
          </div>
          <ChartLegend
            items={dataset.series.map((series, index) => ({
              id: series.id,
              label: series.label,
              color: seriesColor(index),
            }))}
          />
          <div ref={size.ref} className="relative w-full" onMouseLeave={() => setHoveredKey(null)}>
            <svg
              width={chartWidth}
              height={height}
              viewBox={`0 0 ${chartWidth} ${height}`}
              preserveAspectRatio="xMidYMid meet"
              // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps
              // the interactive point controls inside the accessibility tree (see NetworkViewer).
              role="group"
              aria-label={`${dataset.title} expression chart: ${result.samples.length} samples across ${dataset.series.length} series`}
              data-testid="expression-chart-svg"
              className="block w-full rounded-md border border-gray-200 bg-white"
            >
              <ChartAxes
                plot={plot}
                xScale={xScale}
                yScale={yScale}
                yTicks={yTicks}
                xLabel="Sample"
                yLabel={field === 'value' ? 'Expression value' : 'Normalized value'}
                formatValue={formatTickValue}
              />
              <SeriesLines dataset={dataset} xScale={xScale} yScale={yScale} valueField={field} />
              <g data-testid="chart-points">
                {dataset.series.map((series, seriesIndex) => {
                  const color = seriesColor(seriesIndex)
                  return series.points.map((point) => {
                    const value = point[field]
                    if (value === undefined || !Number.isFinite(value)) return null
                    const x = xScale.toPixel(point.sample)
                    const y = yScale.toPixel(value)
                    const pointKey: PointKey = {
                      seriesId: series.id,
                      pointId: point.identifier,
                      sample: point.sample,
                    }
                    const key = keyFor(series, point)
                    const selected = result.selectedKey === key
                    const label = `${series.label}: ${point.identifier} in ${point.sample} = ${formatTooltipValue(value)}`
                    return (
                      <SeriesPoint
                        key={key}
                        x={x}
                        y={y}
                        color={color}
                        label={label}
                        selected={selected}
                        testId={`point-${series.id}-${point.identifier}-${point.sample}`}
                        onMouseEnter={() => setHoveredKey(pointKey)}
                        onMouseLeave={() => setHoveredKey(null)}
                        onSelect={() => result.selectPoint(selected ? null : key)}
                      />
                    )
                  })
                })}
              </g>
            </svg>
            {hovered ? (
              <ChartTooltip
                tooltip={hovered.tooltip}
                x={hovered.x}
                y={hovered.y}
                width={chartWidth}
              />
            ) : null}
          </div>
          <ChartDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}
