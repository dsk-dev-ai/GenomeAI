import { describe, expect, it } from 'vitest'

import { fixtureIntervalGenes, fixtureIntervalVariants } from './genomeBrowser.fixtures'

const TP53_WINDOW = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }

describe('genomeBrowser fixtures', () => {
  it('returns the genes overlapping the TP53 window', () => {
    const genes = fixtureIntervalGenes(TP53_WINDOW)
    expect(genes.map((gene) => gene.name)).toEqual(['TP53', 'ATP5MC1', 'LRRC37A2'])
    expect(genes.every((gene) => gene.type === 'gene')).toBe(true)
  })

  it('returns only genes overlapping a narrower interval', () => {
    const genes = fixtureIntervalGenes({ chromosome: 'chr17', start: 7_670_000, end: 7_685_000 })
    expect(genes.map((gene) => gene.name)).toEqual(['TP53'])
  })

  it('returns no genes for an out-of-window chromosome', () => {
    expect(fixtureIntervalGenes({ chromosome: 'chr1', start: 1, end: 1_000_000 })).toEqual([])
  })

  it('returns the variants whose position falls inside the window', () => {
    const variants = fixtureIntervalVariants(TP53_WINDOW)
    expect(variants).toHaveLength(3)
    expect(variants.map((variant) => variant.variantId)).toEqual([
      'COSM10660',
      'COSM10662',
      'COSM10665',
    ])
  })

  it('returns only variants inside a narrower interval', () => {
    const variants = fixtureIntervalVariants({
      chromosome: 'chr17',
      start: 7_678_540,
      end: 7_678_570,
    })
    expect(variants.map((variant) => variant.variantId)).toEqual(['COSM10665'])
  })

  it('excludes variants whose position falls outside the window', () => {
    const variants = fixtureIntervalVariants({
      chromosome: 'chr17',
      start: 7_650_000,
      end: 7_677_000,
    })
    expect(variants.map((variant) => variant.variantId)).toEqual([])
  })
})
