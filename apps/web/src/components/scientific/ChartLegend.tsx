'use client'

export interface ChartLegendItem {
  id: string
  label: string
  color: string
}

export interface ChartLegendProps {
  items: ChartLegendItem[]
}

/**
 * Reusable series legend: a labelled list of color swatches. Rendered as a
 * semantic list so screen readers announce each series.
 */
export function ChartLegend({ items }: ChartLegendProps) {
  if (items.length === 0) return null
  return (
    <ul
      className="flex w-full flex-wrap items-center gap-x-4 gap-y-1"
      aria-label="Series legend"
      data-testid="chart-legend"
    >
      {items.map((item) => (
        <li key={item.id} className="flex items-center gap-1.5 text-xs text-gray-600">
          <span
            aria-hidden="true"
            className="inline-block h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          {item.label}
        </li>
      ))}
    </ul>
  )
}
