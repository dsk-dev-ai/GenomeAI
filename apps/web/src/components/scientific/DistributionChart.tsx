'use client'

import { useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import type { DistributionDataset } from '@/lib/scientific/advancedTypes'
import { distributionTooltip, valuesForGroup } from '@/lib/scientific/distribution'
import {
  DEFAULT_CHART_HEIGHT,
  DEFAULT_CHART_MARGINS,
  GRIDLINE_TARGET,
  plotArea,
} from '@/lib/scientific/geometry'
import { createCategoryScale, createContinuousScale, formatTickValue } from '@/lib/scientific/scale'
import { formatTooltipValue } from '@/lib/scientific/tooltip'
import { useChartSize } from '@/lib/scientific/useChartSize'
import type {
  DistributionChartResult,
  GroupStatistics,
} from '@/lib/scientific/useDistributionChart'

import { ChartAxes } from './ChartAxes'
import { ChartTooltip } from './ChartTooltip'

const BOX_COLOR = '#2563eb'
const WHISKER_COLOR = '#94a3b8'
const MEDIAN_COLOR = '#0f172a'
const OUTLIER_COLOR = '#dc2626'
const JITTER_RADIUS = 2.5
const HIT_RADIUS = 12

export interface DistributionChartProps {
  /** View model produced by `useDistributionChart`. */
  result: DistributionChartResult
  /** Container heading. */
  title?: string
  /** Optional fixed pixel width (defaults to measured container width). */
  width?: number
  /** Optional fixed pixel height (defaults to `DEFAULT_CHART_HEIGHT`). */
  height?: number
}

/**
 * Distribution Chart (Phase 6.8).
 *
 * Renders a `DistributionDataset` as an interactive SVG box plot: one box per
 * group on the x-axis, summary quartiles/whiskers on the y-axis, individual
 * values overlaid with deterministic jitter, and outliers highlighted. Each
 * group exposes a hover tooltip with its summary statistics. Consumes a
 * `DistributionChartResult` from `useDistributionChart`; all statistics come
 * from `lib/scientific/statistics.ts`.
 */
export function DistributionChart({
  result,
  title = 'Distribution Chart',
  width,
  height = DEFAULT_CHART_HEIGHT,
}: DistributionChartProps) {
  const size = useChartSize(height)
  const chartWidth = width ?? size.width
  const margins = DEFAULT_CHART_MARGINS
  const plot = useMemo(() => plotArea(chartWidth, height, margins), [chartWidth, height, margins])
  const [hoveredGroup, setHoveredGroup] = useState<string | null>(null)

  const dataset = result.dataset
  const description = dataset
    ? dataset.metadata?.description !== undefined
      ? String(dataset.metadata.description)
      : `${result.groups.length} groups`
    : undefined

  const xScale = useMemo(
    () => createCategoryScale(result.groups, [plot.x0, plot.x0 + plot.width], 0.4),
    [result.groups, plot],
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
    if (dataset === undefined || hoveredGroup === null) return null
    const tooltip = distributionTooltip(dataset, hoveredGroup)
    const x = xScale.toPixel(hoveredGroup)
    return { tooltip, x, y: plot.y0 + plot.height / 2 }
  }, [dataset, hoveredGroup, xScale, plot])

  return (
    <VisualizationContainer
      title={title}
      description={description}
      status={result.status}
      error={result.error}
      loadingLabel="Loading distribution data..."
      emptyMessage="No distribution data to show."
      errorTitle="Failed to load distribution data"
      onRetry={result.refetch}
    >
      {result.status === 'success' && dataset ? (
        <div className="flex w-full flex-col gap-2">
          <output className="text-xs text-gray-500" aria-live="polite">
            {result.groups.length} groups · {dataset.values.length} values
          </output>
          <div
            ref={size.ref}
            className="relative w-full"
            onMouseLeave={() => setHoveredGroup(null)}
          >
            <svg
              width={chartWidth}
              height={height}
              viewBox={`0 0 ${chartWidth} ${height}`}
              preserveAspectRatio="xMidYMid meet"
              // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps
              // the interactive group controls inside the accessibility tree (see NetworkViewer).
              role="group"
              aria-label={`${dataset.title} distribution chart: ${result.groups.length} groups`}
              data-testid="distribution-svg"
              className="block w-full rounded-md border border-gray-200 bg-white"
            >
              <ChartAxes
                plot={plot}
                xScale={xScale}
                yScale={yScale}
                yTicks={yTicks}
                xLabel="Group"
                yLabel="Value"
                formatValue={formatTickValue}
              />
              <DistributionBoxes
                result={result}
                dataset={dataset}
                xScale={xScale}
                yScale={yScale}
                onHover={(group) => setHoveredGroup(group)}
                onHoverOut={() => setHoveredGroup(null)}
              />
            </svg>
            {hovered !== null ? (
              <ChartTooltip
                tooltip={hovered.tooltip}
                x={hovered.x}
                y={hovered.y}
                width={chartWidth}
              />
            ) : null}
          </div>
        </div>
      ) : null}
    </VisualizationContainer>
  )
}

function DistributionBoxes({
  result,
  dataset,
  xScale,
  yScale,
  onHover,
  onHoverOut,
}: {
  result: DistributionChartResult
  dataset: DistributionDataset
  xScale: ReturnType<typeof createCategoryScale>
  yScale: ReturnType<typeof createContinuousScale>
  onHover: (group: string) => void
  onHoverOut: () => void
}) {
  return (
    <g data-testid="distribution-boxes">
      {result.statistics.map((entry) => (
        <GroupBox
          key={entry.group}
          entry={entry}
          dataset={dataset}
          xScale={xScale}
          yScale={yScale}
          onHover={onHover}
          onHoverOut={onHoverOut}
        />
      ))}
    </g>
  )
}

function GroupBox({
  entry,
  dataset,
  xScale,
  yScale,
  onHover,
  onHoverOut,
}: {
  entry: GroupStatistics
  dataset: DistributionDataset
  xScale: ReturnType<typeof createCategoryScale>
  yScale: ReturnType<typeof createContinuousScale>
  onHover: (group: string) => void
  onHoverOut: () => void
}) {
  const summary = entry.summary
  const whiskers = entry.whiskers
  const slot = xScale.slot(entry.group)
  const centerX = xScale.toPixel(entry.group)
  if (slot === undefined) return null

  const [focused, setFocused] = useState(false)
  const values = useMemo(() => valuesForGroup(dataset, entry.group), [dataset, entry.group])

  if (summary === undefined) return null

  const boxWidth = Math.max(20, Math.min(60, slot[1] - slot[0] - 12))
  const boxLeft = centerX - boxWidth / 2
  const boxRight = centerX + boxWidth / 2
  const q1Y = yScale.toPixel(summary.q1)
  const q3Y = yScale.toPixel(summary.q3)
  const medianY = yScale.toPixel(summary.q2)
  const topY = yScale.toPixel(whiskers?.upper ?? summary.max)
  const bottomY = yScale.toPixel(whiskers?.lower ?? summary.min)

  const jitteredValues = useMemo(() => {
    const spread = Math.max(0, boxWidth - 14)
    const count = Math.max(1, values.length)
    return values.map((value, index) => {
      const offset = count === 1 ? 0 : (index / (count - 1) - 0.5) * spread
      const isOutlier = whiskers !== undefined && (value < whiskers.lower || value > whiskers.upper)
      return { x: centerX + offset, y: yScale.toPixel(value), outlier: isOutlier, value }
    })
  }, [values, whiskers, centerX, boxWidth, yScale])

  return (
    <g
      data-testid={`group-${entry.group}`}
      onMouseEnter={() => onHover(entry.group)}
      onMouseLeave={onHoverOut}
      onFocus={() => {
        setFocused(true)
        onHover(entry.group)
      }}
      onBlur={() => {
        setFocused(false)
        onHoverOut()
      }}
    >
      <title>{`${entry.group}: median ${formatTooltipValue(summary.q2)}, ${summary.count} values`}</title>
      {/* Whisker line */}
      <line
        x1={centerX}
        y1={topY}
        x2={centerX}
        y2={bottomY}
        stroke={WHISKER_COLOR}
        strokeWidth={1.5}
      />
      {/* Whisker caps */}
      <line
        x1={boxLeft}
        y1={topY}
        x2={boxRight}
        y2={topY}
        stroke={WHISKER_COLOR}
        strokeWidth={1.5}
      />
      <line
        x1={boxLeft}
        y1={bottomY}
        x2={boxRight}
        y2={bottomY}
        stroke={WHISKER_COLOR}
        strokeWidth={1.5}
      />
      {/* Box */}
      <rect
        x={boxLeft}
        y={q3Y}
        width={boxWidth}
        height={Math.max(1, q1Y - q3Y)}
        fill={BOX_COLOR}
        opacity={0.35}
        stroke={BOX_COLOR}
        strokeWidth={1.5}
      />
      {/* Median line */}
      <line
        x1={boxLeft}
        y1={medianY}
        x2={boxRight}
        y2={medianY}
        stroke={MEDIAN_COLOR}
        strokeWidth={2}
      />
      {/* Individual values (deterministic jitter) */}
      {jitteredValues.map((point) => (
        <circle
          key={`${entry.group}-${point.value}-${point.x}`}
          cx={point.x}
          cy={point.y}
          r={JITTER_RADIUS}
          fill={point.outlier ? OUTLIER_COLOR : WHISKER_COLOR}
          opacity={0.8}
          pointerEvents="none"
        />
      ))}
      {focused ? (
        <rect
          x={boxLeft - 6}
          y={topY - 6}
          width={boxWidth + 12}
          height={bottomY - topY + 12}
          fill="none"
          stroke="#0f172a"
          strokeWidth={2}
          strokeDasharray="3 3"
          pointerEvents="none"
          data-testid={`group-${entry.group}-focus-ring`}
        />
      ) : null}
      <rect
        x={centerX - HIT_RADIUS}
        y={topY - HIT_RADIUS}
        width={HIT_RADIUS * 2}
        height={Math.max(0, bottomY - topY) + HIT_RADIUS * 2}
        fill="transparent"
        stroke="none"
        role="button"
        aria-label={`Select group ${entry.group}`}
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') event.preventDefault()
        }}
      />
    </g>
  )
}
