import { describe, expect, it } from 'vitest'

import { createLayout } from './layout'
import { buildTestNetwork } from './network.fixtures'
import {
  DEFAULT_GRAPH_SCALE,
  FIT_PADDING,
  MAX_GRAPH_SCALE,
  MIN_GRAPH_SCALE,
  clampGraphScale,
  fitViewport,
  identityViewport,
  panViewport,
  projectPoint,
  zoomViewport,
} from './viewport'

describe('identityViewport', () => {
  it('starts at scale 1 at the origin', () => {
    expect(identityViewport()).toEqual({ x: 0, y: 0, scale: DEFAULT_GRAPH_SCALE })
  })
})

describe('clampGraphScale', () => {
  it('clamps into the allowed range', () => {
    expect(clampGraphScale(MIN_GRAPH_SCALE)).toBe(MIN_GRAPH_SCALE)
    expect(clampGraphScale(MAX_GRAPH_SCALE)).toBe(MAX_GRAPH_SCALE)
    expect(clampGraphScale(0)).toBe(MIN_GRAPH_SCALE)
    expect(clampGraphScale(100)).toBe(MAX_GRAPH_SCALE)
    expect(clampGraphScale(1)).toBe(1)
  })
})

describe('projectPoint', () => {
  it('applies translation and scale', () => {
    const viewport = { x: 10, y: -5, scale: 2 }
    expect(projectPoint({ x: 3, y: 4 }, viewport)).toEqual({ x: 16, y: 3 })
  })
})

describe('panViewport', () => {
  it('moves by screen pixels and ignores non-finite deltas', () => {
    const viewport = { x: 0, y: 0, scale: 1 }
    expect(panViewport(viewport, 10, -20)).toEqual({ x: 10, y: -20, scale: 1 })
    expect(panViewport(viewport, Number.NaN, 0)).toBe(viewport)
  })
})

describe('zoomViewport', () => {
  it('zooms around a screen point, keeping it fixed', () => {
    const viewport = { x: 0, y: 0, scale: 1 }
    const result = zoomViewport(viewport, 2, 100, 100)
    // Screen point (100,100) maps to layout (0,0) before and after.
    expect(result.scale).toBe(2)
    expect(result.x).toBeCloseTo(100 - 100 * 2)
    expect(result.y).toBeCloseTo(100 - 100 * 2)
  })

  it('clamps the scale to the allowed range', () => {
    const viewport = { x: 0, y: 0, scale: 1 }
    expect(zoomViewport(viewport, 0.0001).scale).toBe(MIN_GRAPH_SCALE)
    expect(zoomViewport(viewport, 1e9).scale).toBe(MAX_GRAPH_SCALE)
  })

  it('returns the viewport unchanged for invalid factors', () => {
    const viewport = { x: 0, y: 0, scale: 1 }
    expect(zoomViewport(viewport, 0)).toBe(viewport)
    expect(zoomViewport(viewport, -1)).toBe(viewport)
    expect(zoomViewport(viewport, Number.NaN)).toBe(viewport)
  })
})

describe('fitViewport', () => {
  it('fits the whole layout centred with padding', () => {
    const layout = createLayout(buildTestNetwork())
    const width = 1000
    const height = 620
    const viewport = fitViewport(layout, width, height)
    // Centre of the layout projects to the centre of the screen.
    const projectedCenter = projectPoint({ x: layout.centerX, y: layout.centerY }, viewport)
    expect(projectedCenter.x).toBeCloseTo(width / 2)
    expect(projectedCenter.y).toBeCloseTo(height / 2)
    // The whole layout fits inside the padded screen area.
    const min = projectPoint({ x: layout.minX, y: layout.minY }, viewport)
    const max = projectPoint({ x: layout.maxX, y: layout.maxY }, viewport)
    expect(min.x).toBeGreaterThanOrEqual(FIT_PADDING - 0.01)
    expect(min.y).toBeGreaterThanOrEqual(FIT_PADDING - 0.01)
    expect(max.x).toBeLessThanOrEqual(width - FIT_PADDING + 0.01)
    expect(max.y).toBeLessThanOrEqual(height - FIT_PADDING + 0.01)
  })

  it('handles single-node layouts with a zero-size bounding box', () => {
    const layout = createLayout({
      id: 'g',
      nodes: [{ id: 'a', label: 'A', type: 'gene' }],
      edges: [],
    })
    const viewport = fitViewport(layout, 1000, 620)
    expect(Number.isFinite(viewport.scale)).toBe(true)
    expect(viewport.scale).toBeGreaterThan(0)
  })
})
