'use client'

import type { PlotArea } from '@/lib/scientific/geometry'
import { categoryLabelTicks } from '@/lib/scientific/scale'
import type { CategoryScale, ContinuousScale } from '@/lib/scientific/scale'

export interface ChartAxesProps {
  /** Data plot area (see `lib/scientific/geometry.ts`). */
  plot: PlotArea
  /** Sample categories on the x-axis. */
  xScale: CategoryScale
  /** Value scale on the y-axis. */
  yScale: ContinuousScale
  /** Ascending tick values to render gridlines + labels for. */
  yTicks: number[]
  /** Optional x-axis caption (e.g. "Sample"). */
  xLabel?: string
  /** Optional y-axis caption (e.g. "Expression value"). */
  yLabel?: string
  /** Renders a tick value as a label (defaults to scientific formatting). */
  formatValue?: (value: number) => string
}

const AXIS_COLOR = '#cbd5e1'
const GRID_COLOR = '#e2e8f0'
const TICK_COLOR = '#475569'
const CAPTION_COLOR = '#94a3b8'

/**
 * Reusable SVG axes for scientific charts: gridlines, y tick labels, the
 * sample labels along the x-axis, and optional axis captions. Pure layout is
 * computed from the supplied scales so the component stays presentation-only.
 */
export function ChartAxes({
  plot,
  xScale,
  yScale,
  yTicks,
  xLabel,
  yLabel,
  formatValue = (value) => String(value),
}: ChartAxesProps) {
  const baselineY = plot.y0 + plot.height
  const sampleTicks = categoryLabelTicks(xScale, plot.width)

  return (
    <g data-testid="chart-axes">
      <g data-testid="chart-grid">
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
      <g data-testid="chart-y-ticks">
        {yTicks.map((tick) => (
          <text
            key={tick}
            x={plot.x0 - 8}
            y={yScale.toPixel(tick)}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={11}
            fill={TICK_COLOR}
          >
            {formatValue(tick)}
          </text>
        ))}
      </g>
      {yLabel !== undefined ? (
        <text
          x={8}
          y={plot.y0 + plot.height / 2}
          transform={`rotate(-90 8 ${plot.y0 + plot.height / 2})`}
          textAnchor="middle"
          fontSize={12}
          fill={CAPTION_COLOR}
          data-testid="chart-y-label"
        >
          {yLabel}
        </text>
      ) : null}
      <g data-testid="chart-x-labels">
        {sampleTicks.map((tick) =>
          tick.visible ? (
            <text
              key={tick.sample}
              x={tick.x}
              y={baselineY + 18}
              textAnchor="middle"
              fontSize={11}
              fill={TICK_COLOR}
            >
              {tick.sample}
            </text>
          ) : null,
        )}
      </g>
      {xLabel !== undefined ? (
        <text
          x={plot.x0 + plot.width / 2}
          y={baselineY + 40}
          textAnchor="middle"
          fontSize={12}
          fill={CAPTION_COLOR}
          data-testid="chart-x-label"
        >
          {xLabel}
        </text>
      ) : null}
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
