import { describe, expect, it } from 'vitest'

import {
  MIN_VIEWPORT_BASES,
  initialViewport,
  panViewport,
  viewportBaseCount,
  wholeContigViewport,
  zoomViewport,
} from './viewport'

describe('viewportBaseCount', () => {
  it('counts one-based inclusive bases', () => {
    expect(viewportBaseCount({ chromosome: 'chr1', start: 1, end: 100 })).toBe(100)
    expect(viewportBaseCount({ chromosome: 'chr1', start: 100, end: 100 })).toBe(1)
  })

  it('never returns less than 1', () => {
    expect(viewportBaseCount({ chromosome: 'chr1', start: 50, end: 40 })).toBe(1)
  })
})

describe('initialViewport', () => {
  it('builds an open-ended window when contig length is unknown', () => {
    const viewport = initialViewport('chr1')
    expect(viewport).toEqual({ chromosome: 'chr1', start: 1, end: 1_000_000, bounds: undefined })
  })

  it('spans the whole contig when its length is known', () => {
    const viewport = initialViewport('chr1', { length: 5000 })
    expect(viewport.end).toBe(5000)
    expect(viewport.bounds).toEqual({ length: 5000 })
  })

  it('honours a custom default window', () => {
    const viewport = initialViewport('chr2', { defaultWindow: 100 })
    expect(viewport.end).toBe(100)
  })
})

describe('wholeContigViewport', () => {
  it('spans the entire contig from base 1', () => {
    const viewport = wholeContigViewport('chr1', { length: 10_000 })
    expect(viewport).toEqual({
      chromosome: 'chr1',
      start: 1,
      end: 10_000,
      bounds: { length: 10_000 },
    })
  })

  it('clamps an empty contig to at least one base', () => {
    const viewport = wholeContigViewport('chrMT', { length: 0 })
    expect(viewport.end).toBe(1)
  })
})

describe('zoomViewport', () => {
  it('zooms around the centre by the given factor', () => {
    const viewport = { chromosome: 'chr1', start: 100, end: 200, bounds: { length: 1000 } }
    const zoomed = zoomViewport(viewport, 0.5)
    // span 101 → Math.round(50.5) = 51
    expect(zoomed.end - zoomed.start + 1).toBe(51)
    expect(zoomed.start).toBeGreaterThanOrEqual(100)
    expect(zoomed.end).toBeLessThanOrEqual(200)
  })

  it('clamps to the contig start when zooming out past it', () => {
    const viewport = { chromosome: 'chr1', start: 1, end: 10, bounds: { length: 1000 } }
    const zoomed = zoomViewport(viewport, 5)
    expect(zoomed.start).toBe(1)
    expect(zoomed.end).toBe(50)
  })

  it('clamps to the contig end when zooming out beyond it', () => {
    const viewport = { chromosome: 'chr1', start: 990, end: 1000, bounds: { length: 1000 } }
    const zoomed = zoomViewport(viewport, 2)
    expect(zoomed.end).toBe(1000)
  })

  it('never zooms below the minimum viewport width', () => {
    const viewport = { chromosome: 'chr1', start: 1, end: 10, bounds: { length: 1000 } }
    const zoomed = zoomViewport(viewport, 0.001)
    expect(zoomed.end - zoomed.start + 1).toBeGreaterThanOrEqual(MIN_VIEWPORT_BASES)
  })

  it('leaves the viewport unchanged for degenerate factors', () => {
    const viewport = { chromosome: 'chr1', start: 1, end: 100, bounds: undefined }
    expect(zoomViewport(viewport, 0)).toBe(viewport)
    expect(zoomViewport(viewport, Number.NaN)).toBe(viewport)
  })
})

describe('panViewport', () => {
  it('shifts the window by the delta', () => {
    const viewport = { chromosome: 'chr1', start: 100, end: 200, bounds: { length: 1000 } }
    const panned = panViewport(viewport, 50)
    expect(panned.start).toBe(150)
    expect(panned.end).toBe(250)
  })

  it('clamps to base 1', () => {
    const viewport = { chromosome: 'chr1', start: 10, end: 20, bounds: { length: 1000 } }
    const panned = panViewport(viewport, -50)
    expect(panned.start).toBe(1)
    expect(panned.end).toBe(11)
  })

  it('clamps to the contig end', () => {
    const viewport = { chromosome: 'chr1', start: 100, end: 200, bounds: { length: 250 } }
    const panned = panViewport(viewport, 400)
    expect(panned.end).toBe(250)
    expect(panned.start).toBe(150)
  })

  it('pans unbounded windows without changing width', () => {
    const viewport = { chromosome: 'chr1', start: 100, end: 200, bounds: undefined }
    const panned = panViewport(viewport, 30)
    expect(panned.start).toBe(130)
    expect(panned.end).toBe(230)
  })
})
