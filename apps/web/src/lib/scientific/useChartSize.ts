/**
 * Responsive chart sizing hook (Phase 6.7).
 *
 * Measures the containing element's width via `ResizeObserver` and falls back
 * to a default width when measurement is unavailable (e.g. during SSR or in
 * jsdom). Height is fixed by the caller. Charts re-render with the measured
 * width so labels and marks stay crisp at any container size.
 */

import { useEffect, useRef, useState } from 'react'

import { DEFAULT_CHART_WIDTH } from './geometry'

export interface ChartSizeResult {
  /** Ref to attach to the chart's wrapper element. */
  ref: React.RefObject<HTMLDivElement | null>
  /** Measured (or fallback) pixel width. */
  width: number
  /** Fixed pixel height. */
  height: number
}

/**
 * Returns the container width (measured) and a fixed height.
 *
 * The initial render uses `fallbackWidth`; once the element is measured the
 * hook updates. If `ResizeObserver` is unavailable the measured width is used
 * once and never re-observed.
 */
export function useChartSize(
  height: number,
  fallbackWidth: number = DEFAULT_CHART_WIDTH,
): ChartSizeResult {
  const ref = useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(fallbackWidth)

  useEffect(() => {
    const element = ref.current
    if (element === null) return
    const update = () => {
      const measured = element.clientWidth
      if (measured > 0) setWidth(measured)
    }
    update()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return { ref, width, height }
}
