import { describe, expect, it } from 'vitest'

import { createScale } from './geometry'
import type { GenomeViewport, VariantFeature } from './types'
import {
  VARIANT_MIN_SEPARATION,
  layoutVariantMarks,
  variantInViewport,
  variantRowY,
  variantTrackHeight,
  variantX,
  variantsInViewport,
} from './variantGeometry'

const viewport: GenomeViewport = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }
const width = 1000

function variant(overrides: Partial<VariantFeature> & { id: string }): VariantFeature {
  return {
    type: 'variant',
    chromosome: 'chr17',
    start: 7_668_000,
    end: 7_668_000,
    position: 7_668_000,
    ...overrides,
  }
}

function scale() {
  return createScale(viewport.start, viewport.end, width)
}

describe('variantInViewport', () => {
  it('keeps variants on the same chromosome inside the inclusive window', () => {
    expect(variantInViewport(variant({ id: 'v1', position: 7_650_000 }), viewport)).toBe(true)
    expect(variantInViewport(variant({ id: 'v2', position: 7_700_000 }), viewport)).toBe(true)
    expect(variantInViewport(variant({ id: 'v3', position: 7_675_000 }), viewport)).toBe(true)
  })

  it('excludes variants outside the window or on another chromosome', () => {
    expect(variantInViewport(variant({ id: 'v4', position: 7_649_999 }), viewport)).toBe(false)
    expect(variantInViewport(variant({ id: 'v5', position: 7_700_001 }), viewport)).toBe(false)
    expect(
      variantInViewport(variant({ id: 'v6', position: 7_675_000, chromosome: 'chr18' }), viewport),
    ).toBe(false)
  })
})

describe('variantsInViewport', () => {
  it('filters a list to the visible window', () => {
    const result = variantsInViewport(
      [
        variant({ id: 'a', position: 7_649_000 }),
        variant({ id: 'b', position: 7_660_000 }),
        variant({ id: 'c', position: 7_701_000 }),
      ],
      viewport,
    )
    expect(result.map((v) => v.id)).toEqual(['b'])
  })
})

describe('variantX', () => {
  it('maps the window start to 0 and each base to a proportional pixel', () => {
    const s = scale()
    expect(variantX(s, viewport.start)).toBeCloseTo(0)
    expect(variantX(s, viewport.start + 1)).toBeCloseTo(s.pxPerBase)
  })

  it('maps the final base just inside the canvas edge', () => {
    const s = scale()
    expect(variantX(s, viewport.end)).toBeCloseTo(width - s.pxPerBase)
  })

  it('maps a mid-window position proportionally', () => {
    const s = scale()
    const mid = Math.floor((viewport.start + viewport.end) / 2)
    expect(variantX(s, mid)).toBeCloseTo((mid - viewport.start) * s.pxPerBase)
  })
})

describe('layoutVariantMarks', () => {
  it('places non-overlapping variants on a single row', () => {
    const s = scale()
    const marks = layoutVariantMarks(s, [
      variant({ id: 'a', position: viewport.start }),
      variant({ id: 'b', position: viewport.start + 1_000 }),
    ])
    expect(marks).toHaveLength(2)
    expect(marks.every((mark) => mark.row === 0)).toBe(true)
  })

  it('stacks variants that land on the same pixel', () => {
    const s = scale()
    const marks = layoutVariantMarks(s, [
      variant({ id: 'a', position: viewport.start }),
      variant({ id: 'b', position: viewport.start }),
      variant({ id: 'c', position: viewport.start }),
    ])
    expect(marks.map((mark) => mark.row)).toEqual([0, 1, 2])
  })

  it('sorts by position then id deterministically', () => {
    const s = scale()
    const marks = layoutVariantMarks(s, [
      variant({ id: 'z', position: viewport.start + 5 }),
      variant({ id: 'a', position: viewport.start }),
    ])
    expect(marks.map((mark) => mark.variant.id)).toEqual(['a', 'z'])
  })

  it('honours a custom minimum separation', () => {
    // 10 bases drawn into 20 px → 2 px per base, so adjacent bases land 2 px
    // apart and stack under the default separation of 5 px.
    const s = createScale(1, 10, 20)
    const tight = layoutVariantMarks(s, [
      variant({ id: 'a', position: 1 }),
      variant({ id: 'b', position: 2 }),
    ])
    expect(tight[1].row).toBeGreaterThan(0)

    // With separation 1 they share a row.
    const loose = layoutVariantMarks(
      s,
      [variant({ id: 'a', position: 1 }), variant({ id: 'b', position: 2 })],
      1,
    )
    expect(loose[1].row).toBe(0)
    expect(VARIANT_MIN_SEPARATION).toBe(5)
  })
})

describe('variantTrackHeight / variantRowY', () => {
  it('keeps at least one row and grows with row count', () => {
    expect(variantTrackHeight(0)).toBe(12)
    expect(variantTrackHeight(1)).toBe(12)
    expect(variantTrackHeight(3)).toBe(36)
  })

  it('centres each stacked row', () => {
    expect(variantRowY(0)).toBe(6)
    expect(variantRowY(1)).toBe(18)
  })
})
