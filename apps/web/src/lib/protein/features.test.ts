import { describe, expect, it } from 'vitest'

import {
  dedupeFeatures,
  featureAccessibleLabel,
  featureDetailLines,
  featureLabel,
  featureTypeColor,
  featureTypeLabel,
  isValidFeature,
  normalizeFeatureType,
  prepareFeatures,
  sortFeatures,
} from './features'
import type { ProteinFeature } from './types'

function feature(overrides: Partial<ProteinFeature> & { id: string }): ProteinFeature {
  return {
    type: 'domain',
    label: 'DNA binding',
    start: 100,
    end: 300,
    ...overrides,
  }
}

describe('normalizeFeatureType', () => {
  it('maps known classes to the canonical literal', () => {
    expect(normalizeFeatureType('domain')).toBe('domain')
    expect(normalizeFeatureType('signal_peptide')).toBe('signal_peptide')
  })

  it('preserves unknown database-specific types verbatim', () => {
    expect(normalizeFeatureType('nuclear-localization-signal')).toBe('nuclear-localization-signal')
  })

  it('treats an empty type as custom', () => {
    expect(normalizeFeatureType('  ')).toBe('custom')
  })
})

describe('featureTypeColor / featureTypeLabel', () => {
  it('returns a colour for known and unknown types', () => {
    expect(featureTypeColor('domain')).toBe('#2563eb')
    expect(typeof featureTypeColor('my-db-term')).toBe('string')
  })

  it('labels types readably', () => {
    expect(featureTypeLabel('signal_peptide')).toBe('signal peptide')
  })
})

describe('isValidFeature', () => {
  it('accepts a valid 1-based inclusive span', () => {
    expect(isValidFeature(feature({ id: 'f1', start: 1, end: 1 }), 393)).toBe(true)
    expect(isValidFeature(feature({ id: 'f2' }))).toBe(true)
  })

  it('rejects invalid ranges and out-of-protein spans', () => {
    expect(isValidFeature(feature({ id: 'f3', start: 0, end: 10 }))).toBe(false)
    expect(isValidFeature(feature({ id: 'f4', start: 50, end: 40 }))).toBe(false)
    expect(isValidFeature(feature({ id: 'f5', start: 300, end: 400 }), 393)).toBe(false)
    expect(isValidFeature({ ...feature({ id: '' }), id: '' })).toBe(false)
  })
})

describe('sortFeatures / dedupeFeatures / prepareFeatures', () => {
  it('sorts deterministically by start, end, then id', () => {
    const sorted = sortFeatures([
      feature({ id: 'b', start: 100, end: 200 }),
      feature({ id: 'a', start: 100, end: 150 }),
      feature({ id: 'c', start: 50, end: 80 }),
    ])
    expect(sorted.map((f) => f.id)).toEqual(['c', 'a', 'b'])
  })

  it('drops duplicate ids keeping the first', () => {
    const deduped = dedupeFeatures([
      feature({ id: 'x', start: 1, end: 10 }),
      feature({ id: 'x', start: 20, end: 30 }),
    ])
    expect(deduped).toHaveLength(1)
    expect(deduped[0].start).toBe(1)
  })

  it('prepares a clean, ordered list', () => {
    const prepared = prepareFeatures(
      [
        feature({ id: 'dup', start: 5, end: 20 }),
        feature({ id: 'bad', start: 0, end: 5 }),
        feature({ id: 'dup', start: 90, end: 100 }),
      ],
      393,
    )
    expect(prepared).toHaveLength(1)
    expect(prepared[0].id).toBe('dup')
  })
})

describe('featureLabel / featureAccessibleLabel / featureDetailLines', () => {
  it('labels a feature by its label field, falling back to type + span', () => {
    expect(featureLabel(feature({ id: 'f1' }))).toBe('DNA binding')
    expect(featureLabel(feature({ id: 'f2', label: '' }))).toBe('domain 100-300')
  })

  it('builds an accessible name', () => {
    expect(featureAccessibleLabel(feature({ id: 'f1' }))).toContain('residues 100-300')
  })

  it('renders detail lines from the reported fields', () => {
    const lines = featureDetailLines(
      feature({
        id: 'f1',
        description: 'binds DNA',
        accession: 'IPR012345',
        metadata: { score: 0.9 },
      }),
    )
    expect(lines.some((line) => line.label === 'Residues' && line.value === '100-300')).toBe(true)
    expect(lines.some((line) => line.label === 'Accession' && line.value === 'IPR012345')).toBe(
      true,
    )
    expect(lines.some((line) => line.label === 'score' && line.value === '0.9')).toBe(true)
  })
})
