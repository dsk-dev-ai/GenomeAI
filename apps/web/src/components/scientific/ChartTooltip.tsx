'use client'

import type { PointTooltip } from '@/lib/scientific/tooltip'

export interface ChartTooltipProps {
  tooltip: PointTooltip
  /** Pixel position of the hovered point (SVG coordinates). */
  x: number
  y: number
  /** Chart canvas width, used to keep the tooltip on-screen. */
  width: number
}

/**
 * Reusable hover tooltip for scientific charts. Rendered as an absolutely
 * positioned HTML element over the SVG; the same `PointTooltip` rows feed the
 * accessible detail panel, so both surfaces stay in sync.
 */
export function ChartTooltip({ tooltip, x, y, width }: ChartTooltipProps) {
  const left = Math.min(Math.max(x + 16, 4), Math.max(width - 240, 4))
  const top = Math.max(y - 8, 4)
  return (
    <div
      data-testid="chart-tooltip"
      className="pointer-events-none absolute z-10 w-56 rounded-md border border-gray-200 bg-white p-2 shadow-md"
      style={{ left, top }}
      role="tooltip"
    >
      <p className="truncate text-xs font-semibold text-gray-900">{tooltip.title}</p>
      <p className="truncate text-xs text-gray-500">{tooltip.subtitle}</p>
      <dl className="mt-1 grid w-full grid-cols-[auto_1fr] gap-x-3 gap-y-0.5">
        {tooltip.rows.map((row) => (
          <div key={row.label} className="contents">
            <dt className="text-xs text-gray-500">{row.label}</dt>
            <dd className="truncate text-xs text-gray-900">{row.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
