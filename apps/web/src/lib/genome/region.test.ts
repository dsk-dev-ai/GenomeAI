import { describe, expect, it } from 'vitest'

import { parseGenomeRegion } from './region'

describe('parseGenomeRegion', () => {
  it('parses a valid chr region into a one-based interval', () => {
    const result = parseGenomeRegion('chr1:100000-200000')
    expect(result).toEqual({
      ok: true,
      interval: { chromosome: 'chr1', start: 100000, end: 200000 },
    })
  })

  it('accepts a prefixless chromosome and normalizes it', () => {
    const result = parseGenomeRegion('7:1-1000')
    expect(result).toEqual({ ok: true, interval: { chromosome: 'chr7', start: 1, end: 1000 } })
  })

  it('accepts sex chromosomes', () => {
    const result = parseGenomeRegion('chrX:500000-600000')
    expect(result.ok && result.interval.chromosome).toBe('chrX')
  })

  it('accepts whitespace around the chromosome', () => {
    const result = parseGenomeRegion(' chr2:1-100 ')
    expect(result.ok && result.interval.start).toBe(1)
  })

  it('rejects malformed input', () => {
    for (const input of [
      'chr1',
      'chr1:100000',
      'chr1:100000-',
      'chr1:-200000',
      'garbage',
      'chr1:100000..200000',
    ]) {
      const result = parseGenomeRegion(input)
      expect(result.ok).toBe(false)
      if (!result.ok) expect(result.error.code).toBe('malformed')
    }
  })

  it('rejects an invalid chromosome', () => {
    const result = parseGenomeRegion('chr0:1-100')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('invalid_chromosome')
  })

  it('rejects non-digit coordinates as malformed', () => {
    const result = parseGenomeRegion('chr1:abc-200000')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('malformed')
  })

  it('rejects negative coordinates', () => {
    const start = parseGenomeRegion('chr1:-100-200000')
    if (start.ok) throw new Error('expected failure')
    expect(start.error.code).toBe('negative_start')

    const end = parseGenomeRegion('chr1:100--200000')
    if (end.ok) throw new Error('expected failure')
    expect(end.error.code).toBe('negative_end')
  })

  it('rejects start after end', () => {
    const result = parseGenomeRegion('chr1:200000-100000')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('start_after_end')
  })
})
