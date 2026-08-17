import { afterEach, describe, expect, it, vi } from 'vitest'

import { GenomeApiError } from '@/lib/genome/api'

import { fetchMolecularStructure, toStructure } from './api'

const rawFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = rawFetch
  vi.restoreAllMocks()
})

function jsonResponse(payload: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(payload),
  } as Response
}

describe('toStructure', () => {
  it('normalizes a raw structure record', () => {
    const structure = toStructure({
      id: 'fixture-mini-p53-helix',
      name: 'p53 N-terminal helix',
      kind: 'protein',
      organism: 'Homo sapiens',
      description: 'Synthetic.',
      chains: [{ id: 'A', residues: [{ index: 1, name: 'MET', atom_indices: [1, 2, 3] }] }],
      atoms: [
        {
          index: 1,
          element: 'N',
          atom_name: 'N',
          residue_name: 'MET',
          residue_index: 1,
          chain_id: 'A',
          x: 0,
          y: 0,
          z: 0,
        },
        {
          serial: 2,
          element_symbol: 'C',
          position_x: 1,
          position_y: 1,
          position_z: 1,
          residue: 1,
          chain: 'A',
        },
        { index: 3, element: 'O', x: 2, y: 2, z: 2, residue_index: 1, chain_id: 'A' },
      ],
      bonds: [
        { atom_a: 1, atom_b: 2, order: 1 },
        { atom1: 2, atom2: 3 },
      ],
      metadata: { source: 'fixture', numeric: 3 },
    })

    expect(structure.id).toBe('fixture-mini-p53-helix')
    expect(structure.name).toBe('p53 N-terminal helix')
    expect(structure.kind).toBe('protein')
    expect(structure.organism).toBe('Homo sapiens')
    expect(structure.chains[0].residues[0].name).toBe('MET')
    expect(structure.atoms).toHaveLength(3)
    expect(structure.atoms[1].element).toBe('C')
    expect(structure.atoms[1].x).toBe(1)
    expect(structure.atoms[1].residueIndex).toBe(1)
    expect(structure.atoms[1].chainId).toBe('A')
    expect(structure.bonds).toEqual([
      { atomA: 1, atomB: 2, order: 1 },
      { atomA: 2, atomB: 3 },
    ])
    expect(structure.metadata).toEqual({ source: 'fixture', numeric: 3 })
  })

  it('drops malformed atoms and bonds while keeping well-formed ones', () => {
    const structure = toStructure({
      id: 'partial',
      atoms: [
        { index: 1, element: 'C', x: 0, y: 0, z: 0, residue_index: 1 },
        { index: 2, element: 'N' },
      ],
      bonds: [{ atom_a: 1, atom_b: 2 }, { atom_b: 1 }],
    })
    expect(structure.atoms).toHaveLength(1)
    expect(structure.bonds).toHaveLength(1)
  })

  it('falls back to molecule_type for the kind and omits unknown kinds', () => {
    expect(toStructure({ id: 'x', molecule_type: 'nucleic-acid' }).kind).toBe('nucleic-acid')
    expect(toStructure({ id: 'x', kind: 'virus' }).kind).toBeUndefined()
  })

  it('filters non-scalar metadata values', () => {
    const structure = toStructure({ id: 'x', metadata: { source: 'fixture', nested: { a: 1 } } })
    expect(structure.metadata).toEqual({ source: 'fixture' })
  })

  it('defaults the id to an empty string and optional fields to undefined', () => {
    const structure = toStructure({})
    expect(structure.id).toBe('')
    expect(structure.name).toBeUndefined()
    expect(structure.chains).toEqual([])
    expect(structure.atoms).toEqual([])
    expect(structure.bonds).toEqual([])
  })
})

describe('fetchMolecularStructure', () => {
  it('fetches, normalizes, and validates a structure', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({
        id: 'a1b2c3',
        name: 'Minimal',
        chains: [{ id: 'A', residues: [{ index: 1, atom_indices: [1] }] }],
        atoms: [{ index: 1, element: 'C', x: 0, y: 0, z: 0, residue_index: 1, chain_id: 'A' }],
        bonds: [],
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const structure = await fetchMolecularStructure('a1b2c3', new AbortController().signal)
    expect(structure.id).toBe('a1b2c3')
    expect(structure.atoms).toHaveLength(1)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/structures/a1b2c3',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
  })

  it('throws a GenomeApiError for a non-2xx response', async () => {
    globalThis.fetch = vi.fn(async () => jsonResponse({}, 404)) as unknown as typeof fetch
    await expect(fetchMolecularStructure('missing')).rejects.toMatchObject({
      name: 'GenomeApiError',
      status: 404,
    })
  })

  it('throws a GenomeApiError for an invalid payload', async () => {
    globalThis.fetch = vi.fn(async () => jsonResponse(null)) as unknown as typeof fetch
    await expect(fetchMolecularStructure('a1b2c3')).rejects.toThrow(GenomeApiError)
  })

  it('throws a GenomeApiError when the payload does not describe a valid structure', async () => {
    globalThis.fetch = vi.fn(async () =>
      jsonResponse({ id: 'empty', atoms: [] }),
    ) as unknown as typeof fetch
    await expect(fetchMolecularStructure('a1b2c3')).rejects.toThrow(GenomeApiError)
  })
})
