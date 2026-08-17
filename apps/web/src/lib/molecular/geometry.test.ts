import { describe, expect, it } from 'vitest'

import {
  backboneTrace,
  cameraFocusForStructure,
  elementColor,
  elementCounts,
  elementPresentation,
  structureBounds,
  structureCentroid,
  structureRadius,
  structureSummary,
} from './geometry'
import type { MolecularStructure } from './types'

function structure(overrides: Partial<MolecularStructure> = {}): MolecularStructure {
  return {
    id: 'geom',
    name: 'Test helix',
    chains: [
      {
        id: 'A',
        residues: [
          { index: 1, name: 'ALA', atomIndices: [1, 2] },
          { index: 2, name: 'GLY', atomIndices: [3] },
        ],
      },
      { id: 'B', residues: [{ index: 1, atomIndices: [4] }] },
    ],
    atoms: [
      { index: 1, element: 'C', x: 0, y: 0, z: 0, residueIndex: 1, chainId: 'A', atomName: 'CA' },
      { index: 2, element: 'N', x: 2, y: 0, z: 0, residueIndex: 1, chainId: 'A', atomName: 'N' },
      { index: 3, element: 'O', x: 0, y: 4, z: 0, residueIndex: 2, chainId: 'A', atomName: 'CA' },
      { index: 4, element: 'S', x: 0, y: 0, z: 6, residueIndex: 1, chainId: 'B', atomName: 'CA' },
    ],
    bonds: [
      { atomA: 1, atomB: 2 },
      { atomA: 3, atomB: 4 },
    ],
    ...overrides,
  }
}

describe('elementPresentation', () => {
  it('returns CPK defaults for a known element', () => {
    expect(elementPresentation('C').color).toBe('909090')
    expect(elementPresentation('o').color).toBe('ff0d0d')
  })

  it('falls back to a default presentation for unknown elements', () => {
    expect(elementPresentation('Xe').color).toBe('ff7f7f')
  })

  it('exposes elementColor', () => {
    expect(elementColor('FE')).toBe('e06633')
  })

  it('keeps van der Waals radii for space filling larger than ball radii', () => {
    for (const symbol of ['C', 'N', 'O', 'S', 'P', 'ZN']) {
      const presentation = elementPresentation(symbol)
      expect(presentation.vanDerWaalsRadius).toBeGreaterThan(presentation.ballRadius)
    }
  })
})

describe('structureBounds', () => {
  it('returns undefined for no atoms', () => {
    expect(structureBounds([])).toBeUndefined()
  })

  it('computes the bounding box', () => {
    const bounds = structureBounds(structure().atoms)
    expect(bounds).toEqual({
      min: { x: 0, y: 0, z: 0 },
      max: { x: 2, y: 4, z: 6 },
    })
  })
})

describe('structureCentroid and structureRadius', () => {
  it('returns the mean position', () => {
    expect(structureCentroid(structure().atoms)).toEqual({ x: 0.5, y: 1, z: 1.5 })
  })

  it('returns the origin for an empty structure', () => {
    expect(structureCentroid([])).toEqual({ x: 0, y: 0, z: 0 })
  })

  it('computes the largest distance from the centroid', () => {
    const centroid = structureCentroid(structure().atoms)
    const radius = structureRadius(structure().atoms, centroid)
    expect(radius).toBeCloseTo(Math.sqrt(21.5))
  })
})

describe('cameraFocusForStructure', () => {
  it('frames around the centroid with a minimum radius', () => {
    const focus = cameraFocusForStructure(structure())
    expect(focus.target).toEqual({ x: 0.5, y: 1, z: 1.5 })
    expect(focus.radius).toBeGreaterThanOrEqual(1)
  })
})

describe('backboneTrace', () => {
  it('traces one point per residue, preferring the CA atom', () => {
    const trace = backboneTrace(structure())
    expect(trace.get('A')).toEqual([
      { x: 0, y: 0, z: 0 },
      { x: 0, y: 4, z: 0 },
    ])
    expect(trace.get('B')).toEqual([{ x: 0, y: 0, z: 6 }])
  })

  it('falls back to the first atom of a residue without a CA', () => {
    const modified = structure()
    modified.chains[0].residues[1].atomIndices = [5]
    modified.atoms = [
      ...modified.atoms,
      { index: 5, element: 'C', x: 9, y: 9, z: 9, residueIndex: 2, chainId: 'A', atomName: 'N' },
    ]
    const trace = backboneTrace(modified)
    expect(trace.get('A')?.[1]).toEqual({ x: 9, y: 9, z: 9 })
  })

  it('omits chains with no residues', () => {
    const modified = structure()
    modified.chains = [{ id: 'C', residues: [] }]
    expect(backboneTrace(modified).size).toBe(0)
  })
})

describe('elementCounts and structureSummary', () => {
  it('tallies atoms per element case-insensitively', () => {
    expect(elementCounts(structure().atoms)).toEqual({ C: 1, N: 1, O: 1, S: 1 })
  })

  it('summarizes chains, residues, atoms, and bonds', () => {
    const summary = structureSummary(structure())
    expect(summary.name).toBe('Test helix')
    expect(summary.chains).toBe(2)
    expect(summary.residues).toBe(3)
    expect(summary.atoms).toBe(4)
    expect(summary.bonds).toBe(2)
    expect(summary.elements.C).toBe(1)
    expect(summary.radius).toBeGreaterThan(0)
  })
})
