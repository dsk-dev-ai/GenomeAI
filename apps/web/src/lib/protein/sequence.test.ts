import { describe, expect, it } from 'vitest'

import {
  aminoAcidAt,
  isValidResidueIndex,
  isValidSequence,
  residueAt,
  residuesInWindow,
  sequenceLength,
  sequenceSlice,
} from './sequence'

const SHORT = 'MEEPQSDPSV'
const LONG = 'ACDEFGHIKLMNPQRSTVWY'.repeat(50)

describe('sequenceLength', () => {
  it('returns 0 for an empty sequence', () => {
    expect(sequenceLength('')).toBe(0)
  })

  it('returns 1 for a single residue', () => {
    expect(sequenceLength('M')).toBe(1)
  })

  it('counts a long sequence', () => {
    expect(sequenceLength(LONG)).toBe(1000)
  })
})

describe('isValidSequence', () => {
  it('accepts canonical amino-acid letters', () => {
    expect(isValidSequence(SHORT)).toBe(true)
    expect(isValidSequence('M')).toBe(true)
  })

  it('rejects an empty sequence', () => {
    expect(isValidSequence('')).toBe(false)
  })

  it('rejects non-canonical and ambiguous codes', () => {
    expect(isValidSequence('MEEPQ-X')).toBe(false)
    expect(isValidSequence('MEEPQ*')).toBe(false)
    expect(isValidSequence('MEEPQ2')).toBe(false)
  })
})

describe('aminoAcidAt / residueAt', () => {
  it('reads the first and last residue by 1-based index', () => {
    expect(aminoAcidAt(SHORT, 1)).toBe('M')
    expect(aminoAcidAt(SHORT, 10)).toBe('V')
    expect(residueAt(SHORT, 1)).toEqual({ index: 1, aminoAcid: 'M' })
    expect(residueAt(SHORT, 10)).toEqual({ index: 10, aminoAcid: 'V' })
  })

  it('returns undefined out of range', () => {
    expect(aminoAcidAt(SHORT, 0)).toBeUndefined()
    expect(aminoAcidAt(SHORT, 11)).toBeUndefined()
    expect(aminoAcidAt('', 1)).toBeUndefined()
    expect(residueAt(SHORT, -1)).toBeUndefined()
  })
})

describe('sequenceSlice', () => {
  it('slices a 1-based inclusive window', () => {
    expect(sequenceSlice(SHORT, 1, 4)).toBe('MEEP')
    expect(sequenceSlice(SHORT, 4, 4)).toBe('P')
  })

  it('clamps out-of-range indices to the sequence', () => {
    expect(sequenceSlice(SHORT, 1, 100)).toBe(SHORT)
    expect(sequenceSlice(SHORT, 0, 5)).toBe('MEEPQ')
  })

  it('returns empty for an invalid window', () => {
    expect(sequenceSlice(SHORT, 6, 5)).toBe('')
  })
})

describe('isValidResidueIndex', () => {
  it('accepts in-range 1-based indices only', () => {
    expect(isValidResidueIndex(SHORT, 1)).toBe(true)
    expect(isValidResidueIndex(SHORT, 10)).toBe(true)
    expect(isValidResidueIndex(SHORT, 0)).toBe(false)
    expect(isValidResidueIndex(SHORT, 11)).toBe(false)
    expect(isValidResidueIndex('', 1)).toBe(false)
  })
})

describe('residuesInWindow', () => {
  it('yields residues with correct 1-based indices', () => {
    expect(residuesInWindow(SHORT, 1, 3)).toEqual([
      { index: 1, aminoAcid: 'M' },
      { index: 2, aminoAcid: 'E' },
      { index: 3, aminoAcid: 'E' },
    ])
  })

  it('returns a single residue for a single-position window', () => {
    expect(residuesInWindow(SHORT, 4, 4)).toEqual([{ index: 4, aminoAcid: 'P' }])
  })

  it('clips windows that extend past the sequence ends', () => {
    expect(residuesInWindow(SHORT, 0, 2)).toEqual([
      { index: 1, aminoAcid: 'M' },
      { index: 2, aminoAcid: 'E' },
    ])
    expect(residuesInWindow(SHORT, 9, 20)).toHaveLength(2)
    expect(residuesInWindow(SHORT, 9, 20)[1]).toEqual({ index: 10, aminoAcid: 'V' })
  })

  it('returns [] for an empty sequence or a window outside it', () => {
    expect(residuesInWindow('', 1, 5)).toEqual([])
    expect(residuesInWindow(SHORT, 20, 30)).toEqual([])
  })

  it('handles long sequences without losing indices', () => {
    const window = residuesInWindow(LONG, 501, 520)
    expect(window).toHaveLength(20)
    expect(window[0].index).toBe(501)
    expect(window[0].aminoAcid).toBe(LONG.charAt(500).toUpperCase())
  })
})
