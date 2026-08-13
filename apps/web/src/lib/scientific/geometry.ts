/**
 * Scientific chart geometry (Phase 6.7).
 *
 * Pure layout math for chart rendering: chart/plot dimensions, margins, and
 * the deterministic series color palette. Rendering components consume the
 * computed `PlotArea` and never derive layout themselves, so layout stays
 * testable and identical across runs.
 */

export interface ChartMargins {
  top: number
  right: number
  bottom: number
  left: number
}

/** Default SVG canvas size used when no width/height is measured or given. */
export const DEFAULT_CHART_WIDTH = 960
export const DEFAULT_CHART_HEIGHT = 480

/** Default margins reserved for axes and labels. */
export const DEFAULT_CHART_MARGINS: ChartMargins = {
  top: 24,
  right: 24,
  bottom: 48,
  left: 64,
}

/** Pixel area available for data marks inside the chart canvas. */
export interface PlotArea {
  x0: number
  y0: number
  width: number
  height: number
}

/** Computes the data plot area from a canvas size and margins. */
export function plotArea(
  width: number,
  height: number,
  margins: ChartMargins = DEFAULT_CHART_MARGINS,
): PlotArea {
  return {
    x0: margins.left,
    y0: margins.top,
    width: Math.max(0, width - margins.left - margins.right),
    height: Math.max(0, height - margins.top - margins.bottom),
  }
}

/**
 * Deterministic, colorblind-aware series palette. Colors are assigned by
 * series index and never depend on hash order, so charts are stable across
 * renders and environments.
 */
export const SERIES_COLORS: readonly string[] = [
  '#2563eb',
  '#16a34a',
  '#dc2626',
  '#9333ea',
  '#d97706',
  '#0891b2',
  '#db2777',
  '#4d7c0f',
]

/** Returns the palette color for a series index, cycling deterministically. */
export function seriesColor(index: number): string {
  return SERIES_COLORS[index % SERIES_COLORS.length]
}

/** Number of horizontal gridlines rendered between the min and max ticks. */
export const GRIDLINE_TARGET = 6
