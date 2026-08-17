import { describe, expect, it } from 'vitest'

import { DEFAULT_TRACK_CONFIG, TRACK_ROW_HEIGHT, featuresInViewport, layoutRows } from './tracks'
import type { GenomicFeature } from './types'

function feature(id: string, start: number, end: number): GenomicFeature {
  return { id, type: 'gene', chromosome: 'chr1', start, end }
}

describe('layoutRows', () => {
  it('stacks features whose ends touch the next start (one-based inclusive)', () => {
    const rows = layoutRows([feature('a', 100, 200), feature('b', 200, 250)])
    expect(rows).toHaveLength(2)
    expect(rows[0].features.map((f) => f.id)).toEqual(['a'])
    expect(rows[1].features.map((f) => f.id)).toEqual(['b'])
  })

  it('breaks ties on start and end by id deterministically', () => {
    const rows = layoutRows([
      feature('b', 100, 100),
      feature('a', 100, 100),
      feature('c', 100, 100),
    ])
    expect(rows.map((row) => row.features[0].id)).toEqual(['a', 'b', 'c'])
  })

  it('sets exact y offsets as the row index times the row height', () => {
    const rows = layoutRows([feature('a', 1, 10), feature('b', 5, 15), feature('c', 9, 19)])
    expect(rows.map((row) => row.yOffset)).toEqual([0, TRACK_ROW_HEIGHT, TRACK_ROW_HEIGHT * 2])
  })

  it('stacks overlapping features into separate rows', () => {
    const rows = layoutRows([feature('a', 100, 200), feature('b', 150, 250)])
    expect(rows).toHaveLength(2)
    expect(rows[0].features.map((f) => f.id)).toEqual(['a'])
    expect(rows[1].features.map((f) => f.id)).toEqual(['b'])
  })

  it('shares a row when features do not overlap', () => {
    const rows = layoutRows([feature('a', 100, 200), feature('b', 300, 400)])
    expect(rows).toHaveLength(1)
    expect(rows[0].features.map((f) => f.id).sort()).toEqual(['a', 'b'])
  })

  it('is deterministic regardless of input order', () => {
    const input = [feature('a', 300, 400), feature('b', 100, 200), feature('c', 150, 250)]
    const rows = layoutRows(input)
    expect(rows[0].features.map((f) => f.id)).toEqual(['b', 'a'])
    expect(rows[1].features.map((f) => f.id)).toEqual(['c'])
  })

  it('sets increasing y offsets per row', () => {
    const rows = layoutRows([feature('a', 1, 100), feature('b', 50, 150), feature('c', 90, 190)])
    expect(rows[0].yOffset).toBe(0)
    expect(rows[1].yOffset).toBeGreaterThan(rows[0].yOffset)
    expect(rows[2].yOffset).toBeGreaterThan(rows[1].yOffset)
  })

  it('handles the empty input', () => {
    expect(layoutRows([])).toEqual([])
  })
})

describe('featuresInViewport', () => {
  it('keeps features overlapping the viewport (one-based inclusive)', () => {
    const features = [feature('a', 100, 200), feature('b', 200, 300), feature('c', 301, 400)]
    const keep = featuresInViewport(features, { chromosome: 'chr1', start: 200, end: 300 })
    expect(keep.map((f) => f.id)).toEqual(['a', 'b'])
  })

  it('handles an empty feature list', () => {
    expect(featuresInViewport([], { chromosome: 'chr1', start: 1, end: 100 })).toEqual([])
  })

  it('drops features fully outside the range', () => {
    const features = [feature('a', 1, 50), feature('b', 700, 900)]
    const keep = featuresInViewport(features, { chromosome: 'chr1', start: 100, end: 800 })
    expect(keep).toEqual([features[1]])
  })

  it('drops features whose coordinates overlap but are on another chromosome', () => {
    const other = { ...feature('x', 250, 260), chromosome: 'chr2' }
    const keep = featuresInViewport([other, feature('a', 250, 260)], {
      chromosome: 'chr1',
      start: 200,
      end: 300,
    })
    expect(keep.map((f) => f.id)).toEqual(['a'])
  })
})

describe('default track configuration', () => {
  it('enables the genes and variants tracks by default', () => {
    expect(DEFAULT_TRACK_CONFIG.enabled).toEqual({ genes: true, variants: true })
  })
})
