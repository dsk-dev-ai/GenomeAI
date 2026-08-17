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

  it('rejects coordinates beyond the safe integer range', () => {
    const tooLarge = `${Number.MAX_SAFE_INTEGER}0`
    const result = parseGenomeRegion(`chr1:1-${tooLarge}`)
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('invalid_end')
  })

  it('accepts a single-base interval', () => {
    const result = parseGenomeRegion('chr1:100-100')
    expect(result).toEqual({ ok: true, interval: { chromosome: 'chr1', start: 100, end: 100 } })
  })

  it('accepts the maximum safe integer coordinate', () => {
    const result = parseGenomeRegion(`chr1:1-${Number.MAX_SAFE_INTEGER}`)
    expect(result.ok).toBe(true)
  })

  it('rejects a start beyond the safe integer range', () => {
    const tooLarge = `${Number.MAX_SAFE_INTEGER}0`
    const result = parseGenomeRegion(`chr1:${tooLarge}-200000`)
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('invalid_start')
  })

  it('rejects a start of zero', () => {
    const result = parseGenomeRegion('chr1:0-100')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('negative_start')
  })

  it('rejects an end of zero', () => {
    const result = parseGenomeRegion('chr1:100-0')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('negative_end')
  })

  it('rejects empty and whitespace-only input as malformed', () => {
    for (const input of ['', '   ']) {
      const result = parseGenomeRegion(input)
      expect(result.ok).toBe(false)
      if (!result.ok) expect(result.error.code).toBe('malformed')
    }
  })

  it('normalizes mixed-case chromosomes', () => {
    const upper = parseGenomeRegion('CHR1:1-100')
    expect(upper.ok && upper.interval.chromosome).toBe('chr1')

    const mixed = parseGenomeRegion('ChrX:1-100')
    expect(mixed.ok && mixed.interval.chromosome).toBe('chrX')
  })

  it('accepts the mitochondrial chromosome', () => {
    const result = parseGenomeRegion('chrM:1-100')
    expect(result.ok && result.interval.chromosome).toBe('chrM')
  })

  it('accepts whitespace around the separator', () => {
    const result = parseGenomeRegion('chr1:100 - 200')
    expect(result.ok && result.interval).toEqual({ chromosome: 'chr1', start: 100, end: 200 })
  })

  it('rejects comma-separated coordinates as malformed', () => {
    const result = parseGenomeRegion('chr1:100,000-200,000')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('malformed')
  })

  it('rejects a plus-signed coordinate as malformed', () => {
    const result = parseGenomeRegion('chr1:+100-200')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('malformed')
  })

  it('rejects trailing junk after the interval as malformed', () => {
    const result = parseGenomeRegion('chr1:1-100 extra')
    expect(result.ok).toBe(false)
    if (!result.ok) expect(result.error.code).toBe('malformed')
  })
})
