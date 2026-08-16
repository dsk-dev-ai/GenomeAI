import { describe, expect, it } from 'vitest'

import {
  BRCA1_CONTEXT,
  PRESET_CONTEXTS,
  TP53_CONTEXT,
  contextRegionKey,
  customContextFromInterval,
  regionToViewport,
  researchContextById,
} from './researchContext'

describe('research contexts', () => {
  it('exposes TP53 and BRCA1 preset contexts with valid regions', () => {
    expect(PRESET_CONTEXTS).toEqual([TP53_CONTEXT, BRCA1_CONTEXT])
    for (const context of PRESET_CONTEXTS) {
      expect(context.id).not.toBe('')
      expect(context.label).not.toBe('')
      expect(context.region.start).toBeGreaterThanOrEqual(1)
      expect(context.region.start).toBeLessThanOrEqual(context.region.end)
    }
  })

  it('keeps preset ids unique', () => {
    const ids = new Set(PRESET_CONTEXTS.map((context) => context.id))
    expect(ids.size).toBe(PRESET_CONTEXTS.length)
  })

  it('finds a preset context by id and returns undefined otherwise', () => {
    expect(researchContextById('tp53-locus')).toBe(TP53_CONTEXT)
    expect(researchContextById('brca1-locus')).toBe(BRCA1_CONTEXT)
    expect(researchContextById('missing-context')).toBeUndefined()
  })

  it('converts a region to a viewport without mutating the interval', () => {
    const interval = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }
    const viewport = regionToViewport(interval)
    expect(viewport).toEqual({ chromosome: 'chr17', start: 7_650_000, end: 7_700_000 })
    expect(viewport).not.toBe(interval)
  })

  it('builds a stable, display-independent region key', () => {
    expect(contextRegionKey({ chromosome: 'chr17', start: 7_650_000, end: 7_700_000 })).toBe(
      'chr17:7650000-7700000',
    )
  })

  it('builds a custom context from a region interval', () => {
    const custom = customContextFromInterval({ chromosome: 'chr1', start: 100, end: 200 })
    expect(custom.id).toBe('custom-chr1-100-200')
    expect(custom.label).toBe('chr1:100-200')
    expect(custom.region).toEqual({ chromosome: 'chr1', start: 100, end: 200 })
  })
})
