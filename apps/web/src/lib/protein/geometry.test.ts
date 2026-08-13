import { describe, expect, it } from 'vitest'

import {
  LABEL_GUTTER,
  RESIDUE_LABEL_MIN_PX,
  computeResidueTicks,
  createResidueScale,
  featureToPixels,
  featuresInViewport,
  formatResiduePosition,
  layoutFeatureRows,
  proteinViewerHeight,
  residueCenterX,
  residueFontSize,
  residueX,
  sequenceRowY,
} from './geometry'
import type { ProteinFeature, ProteinViewport } from './types'

const WIDTH = 1000 - LABEL_GUTTER

function feature(overrides: Partial<ProteinFeature> & { id: string }): ProteinFeature {
  return {
    type: 'domain',
    label: 'test',
    start: 100,
    end: 200,
    ...overrides,
  }
}

function viewport(overrides: Partial<ProteinViewport> = {}): ProteinViewport {
  return { start: 1, end: 200, bounds: { length: 200 }, ...overrides }
}

describe('createResidueScale', () => {
  it('maps the first residue to x 0 and the last to the width', () => {
    const scale = createResidueScale(viewport(), WIDTH)
    expect(scale.toX(1)).toBe(0)
    expect(scale.toX(201)).toBeCloseTo(WIDTH)
    expect(scale.pxPerBase).toBeCloseTo(WIDTH / 200)
  })

  it('handles a single-residue window', () => {
    const scale = createResidueScale(viewport({ start: 42, end: 42 }), WIDTH)
    expect(scale.toX(42)).toBe(0)
    expect(scale.toX(43)).toBe(WIDTH)
  })
})

describe('featureToPixels', () => {
  it('maps an in-viewport feature to a pixel span', () => {
    const scale = createResidueScale(viewport(), WIDTH)
    const { span, visible } = featureToPixels(
      scale,
      viewport(),
      feature({ id: 'f1', start: 100, end: 200 }),
    )
    expect(visible).toBe(true)
    expect(span.x).toBeCloseTo(scale.toX(100))
    expect(span.width).toBeCloseTo(scale.spanToPixels(101))
  })

  it('clips features that hang off the viewport edges', () => {
    const scale = createResidueScale(viewport(), WIDTH)
    const left = featureToPixels(scale, viewport(), feature({ id: 'f2', start: -5, end: 50 }))
    expect(left.visible).toBe(true)
    expect(left.span.x).toBe(0)
    const right = featureToPixels(scale, viewport(), feature({ id: 'f3', start: 180, end: 500 }))
    expect(right.visible).toBe(true)
    expect(right.span.x + right.span.width).toBeCloseTo(WIDTH)
  })

  it('reports features fully outside the viewport as invisible', () => {
    const scale = createResidueScale(viewport(), WIDTH)
    const result = featureToPixels(scale, viewport(), feature({ id: 'f4', start: 300, end: 400 }))
    expect(result.visible).toBe(false)
  })
})

describe('residueX / residueCenterX', () => {
  it('centres residue letters on their cell', () => {
    const scale = createResidueScale(viewport(), WIDTH)
    expect(residueX(scale, 1)).toBe(0)
    expect(residueCenterX(scale, 1)).toBeCloseTo(scale.pxPerBase / 2)
    expect(residueCenterX(scale, 10)).toBeCloseTo(scale.toX(10) + scale.pxPerBase / 2)
  })
})

describe('featuresInViewport', () => {
  it('keeps overlapping features and drops the rest', () => {
    const features = [
      feature({ id: 'in', start: 50, end: 120 }),
      feature({ id: 'boundary', start: 200, end: 210 }),
      feature({ id: 'out', start: 300, end: 400 }),
    ]
    const kept = featuresInViewport(features, viewport())
    expect(kept.map((f) => f.id)).toEqual(['in', 'boundary'])
  })
})

describe('layoutFeatureRows', () => {
  it('stacks overlapping features on separate rows', () => {
    const rows = layoutFeatureRows([
      feature({ id: 'a', start: 1, end: 100 }),
      feature({ id: 'b', start: 50, end: 150 }),
    ])
    expect(rows).toHaveLength(2)
    expect(rows[0].features[0].id).toBe('a')
    expect(rows[1].features[0].id).toBe('b')
    expect(rows[1].yOffset).toBeGreaterThan(rows[0].yOffset)
  })

  it('keeps non-overlapping features on the same row', () => {
    const rows = layoutFeatureRows([
      feature({ id: 'a', start: 1, end: 50 }),
      feature({ id: 'b', start: 60, end: 100 }),
    ])
    expect(rows).toHaveLength(1)
    expect(rows[0].features).toHaveLength(2)
  })
})

describe('proteinViewerHeight / sequenceRowY', () => {
  it('grows with the number of feature rows', () => {
    const twoRows = proteinViewerHeight(2)
    const fourRows = proteinViewerHeight(4)
    expect(twoRows).toBeGreaterThan(0)
    expect(fourRows - twoRows).toBeGreaterThan(0)
    expect(sequenceRowY(0)).toBeGreaterThanOrEqual(0)
  })
})

describe('computeResidueTicks', () => {
  it('labels the first and last residues as majors on a small window', () => {
    const ticks = computeResidueTicks(1, 100, 8)
    const majors = ticks.filter((t) => t.major)
    expect(majors.length).toBeGreaterThan(0)
    expect(majors[0].position).toBeGreaterThanOrEqual(1)
    expect(ticks.every((t) => t.position >= 1 && t.position <= 100)).toBe(true)
  })

  it('produces plain integer labels', () => {
    const ticks = computeResidueTicks(1, 2000, 8)
    expect(ticks.some((t) => t.major && !t.label.includes('K') && !t.label.includes('M'))).toBe(
      true,
    )
  })

  it('handles a single-residue window', () => {
    const ticks = computeResidueTicks(42, 42)
    expect(ticks.some((t) => t.major && t.label === '42')).toBe(true)
  })
})

describe('formatResiduePosition', () => {
  it('formats with grouping, no scientific suffixes', () => {
    expect(formatResiduePosition(1234)).toBe('1,234')
    expect(formatResiduePosition(42)).toBe('42')
  })
})

describe('residueFontSize / RESIDUE_LABEL_MIN_PX', () => {
  it('scales within sensible bounds', () => {
    expect(residueFontSize(RESIDUE_LABEL_MIN_PX)).toBeGreaterThan(0)
    expect(residueFontSize(0)).toBeGreaterThan(0)
    expect(residueFontSize(100)).toBeLessThanOrEqual(12)
  })
})
