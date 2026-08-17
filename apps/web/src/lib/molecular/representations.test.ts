import { describe, expect, it } from 'vitest'

import type { RepresentationId } from './representations'
import {
  DEFAULT_REPRESENTATION,
  REPRESENTATIONS,
  isRepresentationId,
  representationLabel,
} from './representations'

describe('REPRESENTATIONS', () => {
  it('covers every supported representation id with labels and descriptions', () => {
    expect(REPRESENTATIONS.map((option) => option.id)).toEqual([
      'cartoon',
      'ball-and-stick',
      'space-filling',
    ])
    for (const option of REPRESENTATIONS) {
      expect(option.label.length).toBeGreaterThan(0)
      expect(option.description.length).toBeGreaterThan(0)
    }
  })

  it('defaults to the cartoon representation', () => {
    expect(DEFAULT_REPRESENTATION).toBe('cartoon')
    expect(REPRESENTATIONS.some((option) => option.id === DEFAULT_REPRESENTATION)).toBe(true)
  })
})

describe('isRepresentationId', () => {
  it('accepts every catalogued id', () => {
    for (const option of REPRESENTATIONS) {
      expect(isRepresentationId(option.id)).toBe(true)
    }
  })

  it('rejects unknown values', () => {
    expect(isRepresentationId('ribbon')).toBe(false)
    expect(isRepresentationId(undefined)).toBe(false)
    expect(isRepresentationId(42)).toBe(false)
  })
})

describe('representationLabel', () => {
  it('returns the control label for a known id', () => {
    expect(representationLabel('ball-and-stick')).toBe('Ball and stick')
    expect(representationLabel('cartoon')).toBe('Cartoon / ribbon')
  })

  it('falls back to the id itself when unknown', () => {
    expect(representationLabel('ribbon' as RepresentationId)).toBe('ribbon')
  })
})
