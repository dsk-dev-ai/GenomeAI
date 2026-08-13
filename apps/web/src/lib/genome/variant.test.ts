import { describe, expect, it } from 'vitest'

import type { Variant } from './variant'
import {
  isValidVariant,
  toVariant,
  variantAccessibleLabel,
  variantDetailLines,
  variantLabel,
} from './variant'

function variant(overrides: Partial<Variant> & { id: string }): Variant {
  return {
    type: 'variant',
    chromosome: 'chr7',
    start: 100,
    end: 100,
    position: 100,
    ...overrides,
  }
}

describe('toVariant', () => {
  it('normalizes a raw variant record', () => {
    const result = toVariant({
      id: 'var-1',
      variant_id: 'rs113488022',
      chromosome: 'chr7',
      position: 140_453_136,
      ref: 'C',
      alt: 'T',
      type: 'snv',
      quality: 99.5,
      filter_status: 'PASS',
      gene_id: 'gene-1',
      description: 'missense',
    })
    expect(result).toMatchObject({
      id: 'var-1',
      variantId: 'rs113488022',
      chromosome: 'chr7',
      position: 140_453_136,
      start: 140_453_136,
      end: 140_453_136,
      ref: 'C',
      alt: 'T',
      name: 'C>T',
      variantType: 'snv',
      quality: 99.5,
      filterStatus: 'PASS',
      geneId: 'gene-1',
      description: 'missense',
    })
  })

  it('falls back to variant_id for id when the record id is missing', () => {
    const result = toVariant({ variant_id: 'rs1', chromosome: 'chr7', position: 10 })
    expect(result.id).toBe('rs1')
  })

  it('returns an empty variant when coordinates are invalid', () => {
    const result = toVariant({ variant_id: 'rs2', chromosome: 'chr7', position: -1 })
    expect(result.position).toBe(0)
    expect(result.chromosome).toBe('')
  })
})

describe('isValidVariant', () => {
  it('accepts a usable 1-based point', () => {
    expect(isValidVariant(variant({ id: 'v1', position: 7_688_456 }))).toBe(true)
  })

  it('rejects zero, negative, and missing positions', () => {
    expect(isValidVariant(variant({ id: 'v2', position: 0 }))).toBe(false)
    expect(isValidVariant(variant({ id: 'v3', position: -5 }))).toBe(false)
    expect(isValidVariant(variant({ id: 'v4', position: 1.5 }))).toBe(false)
  })

  it('rejects variants without a chromosome', () => {
    expect(isValidVariant(variant({ id: 'v5', chromosome: '' }))).toBe(false)
  })

  it('rejects variants without a non-empty identity', () => {
    expect(isValidVariant({ ...variant({ id: 'v6', position: 10 }), id: '' })).toBe(false)
  })
})

describe('variantLabel', () => {
  it('uses ref>alt when both alleles are known', () => {
    expect(variantLabel(variant({ id: 'v1', ref: 'C', alt: 'T' }))).toBe('C>T')
  })

  it('falls back to the accession then the id', () => {
    expect(variantLabel(variant({ id: 'v2', variantId: 'rs9' }))).toBe('rs9')
    expect(variantLabel(variant({ id: 'v3' }))).toBe('v3')
    expect(variantLabel(variant({ id: '', position: 42 }))).toBe('chr7:42')
  })
})

describe('variantAccessibleLabel', () => {
  it('describes position, type, and filter', () => {
    const label = variantAccessibleLabel(
      variant({ id: 'v1', ref: 'C', alt: 'T', variantType: 'snv', filterStatus: 'PASS' }),
    )
    expect(label).toBe('C>T, chr7:100, snv, filter PASS')
  })

  it('works with minimal data', () => {
    expect(variantAccessibleLabel(variant({ id: 'v2', position: 5 }))).toBe('v2, chr7:5')
  })
})

describe('variantDetailLines', () => {
  it('lists position, alleles, type, quality, filter, and metadata', () => {
    const lines = variantDetailLines(
      variant({
        id: 'v1',
        ref: 'C',
        alt: 'T',
        variantType: 'snv',
        quality: 99.5,
        filterStatus: 'PASS',
        variantId: 'rs1',
        geneId: 'gene-1',
        description: 'missense',
      }),
    )
    expect(lines).toEqual([
      { label: 'Position', value: 'chr7:100' },
      { label: 'Alleles', value: 'C>T' },
      { label: 'Type', value: 'snv' },
      { label: 'Quality', value: '99.5' },
      { label: 'Filter', value: 'PASS' },
      { label: 'Accession', value: 'rs1' },
      { label: 'Gene', value: 'gene-1' },
      { label: 'Description', value: 'missense' },
    ])
  })

  it('omits absent fields', () => {
    const lines = variantDetailLines(variant({ id: 'v2' }))
    expect(lines).toEqual([{ label: 'Position', value: 'chr7:100' }])
  })
})
