import { describe, expect, it } from 'vitest'

import type { MolecularStructure } from './types'
import {
  firstStructureError,
  isUsableStructure,
  isValidStructure,
  validateStructure,
} from './validate'

function validStructure(): MolecularStructure {
  return {
    id: 'test-1',
    chains: [{ id: 'A', residues: [{ index: 1, atomIndices: [1, 2] }] }],
    atoms: [
      { index: 1, element: 'C', x: 0, y: 0, z: 0, residueIndex: 1, chainId: 'A' },
      { index: 2, element: 'N', x: 1, y: 1, z: 1, residueIndex: 1, chainId: 'A' },
    ],
    bonds: [{ atomA: 1, atomB: 2 }],
  }
}

function codes(structure: MolecularStructure): string[] {
  return validateStructure(structure).map((issue) => issue.code)
}

describe('validateStructure', () => {
  it('accepts a structurally consistent structure', () => {
    expect(isValidStructure(validStructure())).toBe(true)
    expect(validateStructure(validStructure())).toEqual([])
  })

  it('rejects a missing structure id', () => {
    expect(codes({ ...validStructure(), id: '' })).toContain('structure.missing-id')
  })

  it('rejects an empty structure', () => {
    const issues = codes({ ...validStructure(), atoms: [], bonds: [] })
    expect(issues).toContain('structure.no-atoms')
  })

  it('rejects non-positive and non-integer atom serials', () => {
    expect(
      codes({ ...validStructure(), atoms: [{ ...validStructure().atoms[0], index: 0 }] }),
    ).toContain('atom.invalid-index')
    expect(
      codes({ ...validStructure(), atoms: [{ ...validStructure().atoms[0], index: 1.5 }] }),
    ).toContain('atom.invalid-index')
  })

  it('rejects duplicate atom serials', () => {
    const duplicate = {
      ...validStructure(),
      atoms: [
        { ...validStructure().atoms[0], index: 1 },
        { ...validStructure().atoms[1], index: 1 },
      ],
    }
    expect(codes(duplicate)).toContain('atom.duplicate-index')
  })

  it('rejects non-finite coordinates', () => {
    const structure = {
      ...validStructure(),
      atoms: [{ ...validStructure().atoms[0], x: Number.NaN }],
    }
    expect(codes(structure)).toContain('atom.non-finite-coordinates')
  })

  it('rejects an invalid residue number on an atom', () => {
    const structure = {
      ...validStructure(),
      atoms: [{ ...validStructure().atoms[0], residueIndex: 0 }],
    }
    expect(codes(structure)).toContain('atom.invalid-residue')
  })

  it('rejects atoms without an element', () => {
    const structure = {
      ...validStructure(),
      atoms: [{ ...validStructure().atoms[0], element: '' }],
    }
    expect(codes(structure)).toContain('atom.missing-element')
  })

  it('rejects a bond referencing a missing atom', () => {
    const structure = {
      ...validStructure(),
      bonds: [{ atomA: 1, atomB: 999 }],
    }
    expect(codes(structure)).toContain('bond.dangling')
  })

  it('rejects a bond that joins an atom to itself', () => {
    const structure = {
      ...validStructure(),
      bonds: [{ atomA: 1, atomB: 1 }],
    }
    expect(codes(structure)).toContain('bond.self-loop')
  })

  it('rejects duplicate bonds regardless of endpoint order', () => {
    const structure = {
      ...validStructure(),
      bonds: [
        { atomA: 1, atomB: 2 },
        { atomA: 2, atomB: 1 },
      ],
    }
    expect(codes(structure)).toContain('bond.duplicate')
  })

  it('rejects a chain without an identifier', () => {
    const structure = { ...validStructure(), chains: [{ ...validStructure().chains[0], id: '' }] }
    expect(codes(structure)).toContain('chain.missing-id')
  })

  it('rejects an invalid residue number', () => {
    const structure = {
      ...validStructure(),
      chains: [{ ...validStructure().chains[0], residues: [{ index: 0, atomIndices: [1, 2] }] }],
    }
    expect(codes(structure)).toContain('residue.invalid-index')
  })

  it('rejects duplicate residue numbers within a chain', () => {
    const chain = validStructure().chains[0]
    const structure = {
      ...validStructure(),
      chains: [
        {
          id: chain.id,
          residues: [
            { index: 1, atomIndices: [1] },
            { index: 1, atomIndices: [2] },
          ],
        },
      ],
    }
    expect(codes(structure)).toContain('residue.duplicate-index')
  })

  it('rejects a residue referencing a missing atom', () => {
    const structure = {
      ...validStructure(),
      chains: [{ ...validStructure().chains[0], residues: [{ index: 1, atomIndices: [999] }] }],
    }
    expect(codes(structure)).toContain('residue.dangling-atom')
  })

  it('rejects atoms that belong to no residue', () => {
    const structure = {
      ...validStructure(),
      chains: [{ ...validStructure().chains[0], residues: [{ index: 1, atomIndices: [1] }] }],
    }
    expect(codes(structure)).toContain('atom.unreferenced')
  })

  it('reports every issue found, not just the first', () => {
    const structure: MolecularStructure = {
      id: '',
      chains: [],
      atoms: [{ index: 0, element: '', x: Number.NaN, y: 0, z: 0, residueIndex: 0, chainId: '' }],
      bonds: [],
    }
    const found = codes(structure)
    expect(found).toEqual(
      expect.arrayContaining([
        'structure.missing-id',
        'atom.invalid-index',
        'atom.non-finite-coordinates',
        'atom.invalid-residue',
        'atom.missing-element',
        'atom.unreferenced',
      ]),
    )
  })
})

describe('isUsableStructure and firstStructureError', () => {
  it('is usable for a valid non-empty structure', () => {
    expect(isUsableStructure(validStructure())).toBe(true)
  })

  it('is not usable for an empty structure', () => {
    expect(isUsableStructure({ ...validStructure(), atoms: [], bonds: [] })).toBe(false)
  })

  it('is not usable for a malformed structure', () => {
    expect(isUsableStructure({ ...validStructure(), bonds: [{ atomA: 1, atomB: 999 }] })).toBe(
      false,
    )
  })

  it('returns the first issue message or null', () => {
    expect(firstStructureError(validStructure())).toBeNull()
    const message = firstStructureError({ ...validStructure(), id: '' })
    expect(message).toBe('Structure has no identifier.')
  })
})
