import { describe, expect, it } from 'vitest'

import { isValidChromosome, normalizeChromosome } from './chromosome'

describe('normalizeChromosome', () => {
  it('normalizes autosomes to their canonical chrN form', () => {
    expect(normalizeChromosome('chr1')).toBe('chr1')
    expect(normalizeChromosome('CHR22')).toBe('chr22')
  })

  it('normalizes without the chr prefix', () => {
    expect(normalizeChromosome('7')).toBe('chr7')
    expect(normalizeChromosome('x')).toBe('chrX')
  })

  it('normalizes sex and mitochondrial chromosomes', () => {
    expect(normalizeChromosome('chrX')).toBe('chrX')
    expect(normalizeChromosome('chrY')).toBe('chrY')
    expect(normalizeChromosome('chrMT')).toBe('chrMT')
    expect(normalizeChromosome('M')).toBe('chrM')
  })

  it('rejects invalid identifiers', () => {
    for (const bad of ['chr0', 'chr1.1', 'chr1p', '1p', '', 'chr', 'chrXY', 'chr123']) {
      expect(normalizeChromosome(bad), bad).toBeNull()
    }
  })

  it('trims surrounding whitespace', () => {
    expect(normalizeChromosome('  chr2  ')).toBe('chr2')
  })
})

describe('isValidChromosome', () => {
  it('returns true for valid identifiers', () => {
    expect(isValidChromosome('chr1')).toBe(true)
    expect(isValidChromosome('Y')).toBe(true)
  })

  it('returns false for invalid identifiers', () => {
    expect(isValidChromosome('chr0')).toBe(false)
    expect(isValidChromosome('chr1q')).toBe(false)
  })
})
