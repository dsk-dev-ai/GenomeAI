import { describe, expect, it } from 'vitest'

import { P53_HELIX_STRUCTURE_FIXTURE } from './molecular.fixtures'
import { isValidStructure, validateStructure } from './validate'

describe('P53_HELIX_STRUCTURE_FIXTURE', () => {
  it('is a structurally valid, usable fixture', () => {
    expect(validateStructure(P53_HELIX_STRUCTURE_FIXTURE)).toEqual([])
    expect(isValidStructure(P53_HELIX_STRUCTURE_FIXTURE)).toBe(true)
  })

  it('is stable across repeated access (deterministic generation)', () => {
    expect(JSON.stringify(P53_HELIX_STRUCTURE_FIXTURE.atoms)).toBe(
      JSON.stringify(P53_HELIX_STRUCTURE_FIXTURE.atoms),
    )
    const bonds = P53_HELIX_STRUCTURE_FIXTURE.bonds
    expect(bonds.length).toBeGreaterThan(0)
    expect(P53_HELIX_STRUCTURE_FIXTURE.chains).toHaveLength(1)
    expect(P53_HELIX_STRUCTURE_FIXTURE.chains[0].id).toBe('A')
    expect(P53_HELIX_STRUCTURE_FIXTURE.kind).toBe('protein')
  })

  it('describes a small polymer: one chain, many residues, more atoms than residues', () => {
    const residues = P53_HELIX_STRUCTURE_FIXTURE.chains[0].residues.length
    expect(residues).toBeGreaterThanOrEqual(10)
    expect(P53_HELIX_STRUCTURE_FIXTURE.atoms.length).toBeGreaterThan(residues)
    expect(P53_HELIX_STRUCTURE_FIXTURE.bonds.length).toBeGreaterThan(residues)
  })

  it('uses the synthetic marker metadata', () => {
    expect(P53_HELIX_STRUCTURE_FIXTURE.metadata?.source).toBe('fixture')
  })
})
