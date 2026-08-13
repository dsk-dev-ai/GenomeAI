import { describe, expect, it } from 'vitest'

import type { ProteinViewport } from './types'
import {
  MIN_VIEWPORT_RESIDUES,
  PROTEIN_DEFAULT_WINDOW,
  initialProteinViewport,
  navigateProteinViewport,
  panFraction,
  panProteinViewport,
  parseProteinRegion,
  proteinViewportLength,
  proteinViewportSpan,
  wholeProteinViewport,
  zoomProteinViewport,
} from './viewport'

function vp(overrides: Partial<ProteinViewport> = {}): ProteinViewport {
  return { start: 1, end: 100, bounds: { length: 1000 }, ...overrides }
}

describe('wholeProteinViewport / initialProteinViewport', () => {
  it('builds a full-protein window', () => {
    expect(wholeProteinViewport(393)).toEqual({ start: 1, end: 393, bounds: { length: 393 } })
  })

  it('starts a long protein on the first window, clamped to length', () => {
    expect(initialProteinViewport(393)).toEqual({
      start: 1,
      end: PROTEIN_DEFAULT_WINDOW,
      bounds: { length: 393 },
    })
  })

  it('clamps to proteins shorter than the default window', () => {
    expect(initialProteinViewport(12)).toEqual({ start: 1, end: 12, bounds: { length: 12 } })
  })

  it('handles empty-length proteins defensively', () => {
    const view = wholeProteinViewport(0)
    expect(view.start).toBe(1)
    expect(view.end).toBe(1)
  })
})

describe('proteinViewportLength / proteinViewportSpan', () => {
  it('reads the length from bounds and the visible span from start/end', () => {
    expect(proteinViewportLength(vp())).toBe(1000)
    expect(proteinViewportSpan(vp())).toBe(100)
    expect(proteinViewportLength(wholeProteinViewport(200))).toBe(200)
  })
})

describe('panProteinViewport', () => {
  it('pans within the protein and clamps at the ends', () => {
    expect(panProteinViewport(vp(), 50)).toEqual({ start: 51, end: 150, bounds: { length: 1000 } })
    expect(panProteinViewport(vp(), -200).start).toBe(1)
    expect(panProteinViewport(vp({ start: 950, end: 1000 }), 200).end).toBe(1000)
  })
})

describe('zoomProteinViewport', () => {
  it('zooms in without crossing residue 1', () => {
    const zoomed = zoomProteinViewport(vp(), 1 / 2)
    expect(zoomed.start).toBeGreaterThanOrEqual(1)
    expect(zoomed.end - zoomed.start + 1).toBeLessThanOrEqual(proteinViewportSpan(vp()))
  })

  it('zooms out but never beyond the protein length', () => {
    const zoomed = zoomProteinViewport(vp({ start: 450, end: 550 }), 2)
    expect(zoomed.start).toBeGreaterThanOrEqual(1)
    expect(zoomed.end).toBeLessThanOrEqual(1000)
  })
})

describe('panFraction', () => {
  it('moves a fraction of the visible window in the given direction', () => {
    expect(panFraction(vp(), 1)).toBe(50)
    expect(panFraction(vp(), -1)).toBe(-50)
    expect(panFraction(vp({ start: 1, end: 1 }), -1)).toBeLessThanOrEqual(0)
  })
})

describe('navigateProteinViewport', () => {
  it('jumps to an explicit window', () => {
    expect(navigateProteinViewport(vp(), 200, 300)).toEqual({
      start: 200,
      end: 300,
      bounds: { length: 1000 },
    })
  })

  it('clamps the jump to the protein', () => {
    expect(navigateProteinViewport(vp(), 900, 5000)).toEqual({
      start: 900,
      end: 1000,
      bounds: { length: 1000 },
    })
    expect(navigateProteinViewport(vp(), -10, 5).start).toBe(MIN_VIEWPORT_RESIDUES)
  })

  it('rejects an invalid window', () => {
    expect(navigateProteinViewport(vp(), 50, 40)).toEqual(vp())
  })
})

describe('parseProteinRegion', () => {
  it('parses a single position', () => {
    expect(parseProteinRegion('42', 393)).toEqual({ ok: true, start: 42, end: 42 })
  })

  it('parses a range', () => {
    expect(parseProteinRegion('42-80', 393)).toEqual({ ok: true, start: 42, end: 80 })
  })

  it('clamps single positions and ranges to the protein length', () => {
    expect(parseProteinRegion('500', 393)).toEqual({ ok: true, start: 393, end: 393 })
    expect(parseProteinRegion('380-500', 393)).toEqual({ ok: true, start: 380, end: 393 })
  })

  it('rejects malformed input with a typed error', () => {
    expect(parseProteinRegion('', 393).ok).toBe(false)
    expect(parseProteinRegion('abc', 393).ok).toBe(false)
    expect(parseProteinRegion('0', 393).ok).toBe(false)
    expect(parseProteinRegion('80-42', 393).ok).toBe(false)
    expect(parseProteinRegion('1-2-3', 393).ok).toBe(false)
  })
})
