'use client'

import { useId, useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import type { HeatmapDataset } from '@/lib/scientific/advancedTypes'
import { DEFAULT_CHART_HEIGHT, DEFAULT_CHART_MARGINS, plotArea } from '@/lib/scientific/geometry'
import type { PlotArea } from '@/lib/scientific/geometry'
import {
  heatmapCellKey,
  heatmapCellTooltip,
  heatmapColumnLabel,
  heatmapRowLabel,
  parseHeatmapCellKey,
} from '@/lib/scientific/heatmap'
import { useChartSize } from '@/lib/scientific/useChartSize'
import type { HeatmapResult } from '@/lib/scientific/useHeatmap'

import { ChartTooltip } from './ChartTooltip'

const AXIS_COLOR = '#cbd5e1'
const MISSING_FILL = '#eef2f7'

export interface HeatmapProps {
  /** View model produced by `useHeatmap`. */
  result: HeatmapResult
  /** Container heading. */
  title?: string
  /** Optional fixed pixel width (defaults to measured container width). */
  width?: number
  /** Optional fixed pixel height (defaults to `DEFAULT_CHART_HEIGHT`). */
  height?: number
}

/**
 * Heatmap (Phase 6.8).
 *
 * Renders a `HeatmapDataset` as an interactive SVG grid of cells: rows on the
 * y-axis, columns on the x-axis, and a diverging color scale mapping each
 * value. Missing values render as a distinct neutral cell. Cells expose hover
 * tooltips and keyboard-accessible selection with a readable detail panel.
 * Consumes a `HeatmapResult` from `useHeatmap`; all data transformation stays
 * in `lib/scientific`.
 */
export function Heatmap({
  result,
  title = 'Heatmap',
  width,
  height = DEFAULT_CHART_HEIGHT,
}: HeatmapProps) {
  const size = useChartSize(height)
  const chartWidth = width ?? size.width
  const margins = DEFAULT_CHART_MARGINS
  const plot = useMemo(() => plotArea(chartWidth, height, margins), [chartWidth, height, margins])
  const [hoveredKey, setHoveredKey] = useState<string | null>(null)
  const [hoveredPosition, setHoveredPosition] = useState<{ x: number; y: number } | null>(null)

  const dataset = result.dataset
  const description = dataset
    ? dataset.metadata?.description !== undefined
      ? String(dataset.metadata.description)
      : `${dataset.rows.length} rows · ${dataset.columns.length} columns`
    : undefined

  return (
    <VisualizationContainer
      title={title}
      description={description}
      status={result.status}
      error={result.error}
      loadingLabel="Loading heatmap data..."
      emptyMessage="No heatmap data to show."
      errorTitle="Failed to load heatmap data"
      onRetry={result.refetch}
    >
      {result.status === 'success' && dataset ? (
        <div className="flex w-full flex-col gap-2">
          <output className="text-xs text-gray-500" aria-live="polite">
            {dataset.rows.length} rows · {dataset.columns.length} columns
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
              // the interactive cell controls inside the accessibility tree (see NetworkViewer).
              role="group"
              aria-label={`${dataset.title} heatmap: ${dataset.rows.length} rows across ${dataset.columns.length} columns`}
              data-testid="heatmap-svg"
              className="block w-full rounded-md border border-gray-200 bg-white"
            >
              <HeatmapGrid
                dataset={dataset}
                plot={plot}
                colorScale={result.colorScale}
                selectedKey={result.selectedKey}
                onHover={(key, position) => {
                  setHoveredKey(key)
                  setHoveredPosition(position)
                }}
                onSelect={result.selectCell}
              />
            </svg>
            {hoveredKey !== null && hoveredPosition !== null ? (
              <HeatmapHoverTooltip
                dataset={dataset}
                cellKey={hoveredKey}
                position={hoveredPosition}
                width={chartWidth}
              />
            ) : null}
          </div>
          <HeatmapDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}

function HeatmapGrid({
  dataset,
  plot,
  colorScale,
  selectedKey,
  onHover,
  onSelect,
}: {
  dataset: HeatmapDataset
  plot: PlotArea
  colorScale: (value: number) => string
  selectedKey: string | null
  onHover: (key: string, position: { x: number; y: number }) => void
  onSelect: (key: string | null) => void
}) {
  const rows = dataset.rows.length
  const columns = dataset.columns.length
  const rowStep = rows > 0 ? plot.height / rows : 0
  const columnStep = columns > 0 ? plot.width / columns : 0

  return (
    <g data-testid="heatmap-grid">
      <HeatmapAxes dataset={dataset} plot={plot} rowStep={rowStep} columnStep={columnStep} />
      {dataset.rows.map((row, rowIndex) =>
        dataset.columns.map((column, columnIndex) => {
          const value = dataset.values[rowIndex]?.[columnIndex]
          const key = heatmapCellKey({ row, column })
          const selected = selectedKey === key
          const missing = value === undefined
          const color = missing ? MISSING_FILL : colorScale(value)
          const x = plot.x0 + columnIndex * columnStep
          const y = plot.y0 + rowIndex * rowStep
          const label = missing
            ? `${heatmapRowLabel(dataset, row)} · ${heatmapColumnLabel(dataset, column)} · no measurement`
            : `${heatmapRowLabel(dataset, row)} · ${heatmapColumnLabel(dataset, column)} = ${value}`
          return (
            <rect
              key={key}
              data-testid={`cell-${row}-${column}`}
              x={x}
              y={y}
              width={columnStep}
              height={rowStep}
              fill={color}
              stroke={selected ? '#0f172a' : AXIS_COLOR}
              strokeWidth={selected ? 2 : 0.5}
              role="button"
              aria-label={`Select ${label}`}
              aria-pressed={selected}
              tabIndex={0}
              onMouseEnter={() => onHover(key, { x: x + columnStep / 2, y: y + rowStep / 2 })}
              onMouseLeave={() => onHover('', { x: 0, y: 0 })}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  onSelect(selected ? null : key)
                }
              }}
              onClick={(event) => {
                event.stopPropagation()
                onSelect(selected ? null : key)
              }}
            />
          )
        }),
      )}
    </g>
  )
}

function HeatmapAxes({
  dataset,
  plot,
  rowStep,
  columnStep,
}: {
  dataset: HeatmapDataset
  plot: PlotArea
  rowStep: number
  columnStep: number
}) {
  return (
    <g data-testid="heatmap-axes">
      {dataset.columns.map((column, index) => {
        const x = plot.x0 + index * columnStep + columnStep / 2
        return (
          <text
            key={`column-${column}`}
            x={x}
            y={plot.y0 - 8}
            textAnchor="middle"
            fontSize={11}
            fill="#475569"
          >
            {heatmapColumnLabel(dataset, column)}
          </text>
        )
      })}
      {dataset.rows.map((row, index) => {
        const y = plot.y0 + index * rowStep + rowStep / 2
        return (
          <text
            key={`row-${row}`}
            x={plot.x0 - 8}
            y={y}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={11}
            fill="#475569"
          >
            {heatmapRowLabel(dataset, row)}
          </text>
        )
      })}
      <line
        x1={plot.x0}
        y1={plot.y0}
        x2={plot.x0 + plot.width}
        y2={plot.y0}
        stroke={AXIS_COLOR}
        strokeWidth={1}
      />
      <line
        x1={plot.x0}
        y1={plot.y0}
        x2={plot.x0}
        y2={plot.y0 + plot.height}
        stroke={AXIS_COLOR}
        strokeWidth={1}
      />
    </g>
  )
}

function HeatmapHoverTooltip({
  dataset,
  cellKey,
  position,
  width,
}: {
  dataset: HeatmapDataset
  cellKey: string
  position: { x: number; y: number }
  width: number
}) {
  const coords = parseHeatmapCellKey(cellKey)
  if (coords === undefined) return null
  const rowIndex = dataset.rows.indexOf(coords.row)
  const columnIndex = dataset.columns.indexOf(coords.column)
  const value =
    rowIndex >= 0 && columnIndex >= 0 ? dataset.values[rowIndex]?.[columnIndex] : undefined
  const tooltip = heatmapCellTooltip(dataset, coords.row, coords.column, value)
  return <ChartTooltip tooltip={tooltip} x={position.x} y={position.y} width={width} />
}

function HeatmapDetail({ result }: { result: HeatmapResult }) {
  const dataset = result.dataset
  const selectedKey = result.selectedKey
  const headingId = useId()
  if (dataset === undefined || selectedKey === null) return null

  const coords = parseHeatmapCellKey(selectedKey)
  if (coords === undefined) return null
  const rowIndex = dataset.rows.indexOf(coords.row)
  const columnIndex = dataset.columns.indexOf(coords.column)
  const value =
    rowIndex >= 0 && columnIndex >= 0 ? dataset.values[rowIndex]?.[columnIndex] : undefined
  const tooltip = heatmapCellTooltip(dataset, coords.row, coords.column, value)
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby={headingId}
      data-testid="heatmap-selection-detail"
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
