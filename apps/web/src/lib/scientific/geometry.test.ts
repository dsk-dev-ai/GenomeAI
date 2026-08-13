import { describe, expect, it } from 'vitest'

import { DEFAULT_CHART_MARGINS, plotArea, seriesColor } from './geometry'
import { SERIES_COLORS } from './geometry'

describe('plotArea', () => {
  it('subtracts margins from the canvas size', () => {
    const area = plotArea(960, 480, DEFAULT_CHART_MARGINS)
    expect(area.x0).toBe(DEFAULT_CHART_MARGINS.left)
    expect(area.y0).toBe(DEFAULT_CHART_MARGINS.top)
    expect(area.width).toBe(960 - DEFAULT_CHART_MARGINS.left - DEFAULT_CHART_MARGINS.right)
    expect(area.height).toBe(480 - DEFAULT_CHART_MARGINS.top - DEFAULT_CHART_MARGINS.bottom)
  })

  it('clamps to a non-negative size for tiny canvases', () => {
    const area = plotArea(20, 20, DEFAULT_CHART_MARGINS)
    expect(area.width).toBeGreaterThanOrEqual(0)
    expect(area.height).toBeGreaterThanOrEqual(0)
  })

  it('uses default margins when none are given', () => {
    expect(plotArea(960, 480).x0).toBe(DEFAULT_CHART_MARGINS.left)
  })
})

describe('seriesColor', () => {
  it('returns the palette color for a series index', () => {
    expect(seriesColor(0)).toBe('#2563eb')
    expect(seriesColor(1)).toBe('#16a34a')
  })

  it('cycles deterministically past the palette end', () => {
    expect(seriesColor(0)).toBe(seriesColor(SERIES_COLORS.length))
  })
})
