/**
 * Development fixture for the Molecular Structure Viewer (Phase 6.12).
 *
 * The GenomeAI backend does **not yet expose any molecular structure
 * endpoint**. This module provides a small, clearly isolated, synthetic
 * structure that mimics what a future structure source would return, so the
 * viewer, its geometry math, and its tests can be developed now.
 *
 * ## Boundary
 *
 * This is a **development fixture, not a real API or a real molecule**. It is
 * generated deterministically (a straight alpha-helix-like trace with
 * backbone atoms N/CA/C/O per residue and a few side-chain atoms) purely so
 * the 3D rendering pipeline has realistic input. It flows through the same
 * `toStructure` normalizer the production adapter uses, so the seam is
 * exercised exactly as production would. See
 * `docs/visualization/molecular-structure.md`.
 */

import { type RawStructureRecord, toStructure } from './api'
import type { MolecularStructure } from './types'

const RESIDUE_NAMES = [
  'MET',
  'GLU',
  'GLU',
  'PRO',
  'GLN',
  'SER',
  'ASP',
  'PRO',
  'SER',
  'VAL',
  'GLU',
  'PRO',
  'PRO',
  'LEU',
  'SER',
]

const RESIDUES_COUNT = RESIDUE_NAMES.length
const HELIX_RADIUS = 4.5
const RISE_PER_RESIDUE = 1.5
const RESIDUES_PER_TURN = 3.6

/**
 * Synthetic raw structure record: a short alpha-helix-like trace over the
 * N-terminal residues of TP53. Coordinates are generated deterministically
 * (no random values), so the fixture is stable for tests and rendering.
 */
function buildRawFixture(): RawStructureRecord {
  const atoms: unknown[] = []
  const bonds: unknown[] = []
  const residues: unknown[] = []
  const chainId = 'A'

  let serial = 0
  const previousCarbon: number[] = []
  const cAlphaByResidue: number[] = []

  for (let residueIndex = 0; residueIndex < RESIDUES_COUNT; residueIndex++) {
    const angle = (residueIndex / RESIDUES_PER_TURN) * 2 * Math.PI
    const z = residueIndex * RISE_PER_RESIDUE
    const caX = HELIX_RADIUS * Math.cos(angle)
    const caY = HELIX_RADIUS * Math.sin(angle)

    const backbone = [
      { name: 'N', dx: 0.5, dy: 0.4, dz: -0.6 },
      { name: 'CA', dx: 0, dy: 0, dz: 0 },
      { name: 'C', dx: -0.4, dy: -0.5, dz: 0.6 },
      { name: 'O', dx: -0.9, dy: -0.6, dz: 0.6 },
    ]

    const residueAtoms: number[] = []
    for (const position of backbone) {
      serial += 1
      residueAtoms.push(serial)
      const isCarbon = position.name === 'CA' || position.name === 'C'
      atoms.push({
        index: serial,
        element: position.name === 'O' ? 'O' : isCarbon ? 'C' : 'N',
        atom_name: position.name,
        residue_name: RESIDUE_NAMES[residueIndex],
        residue_index: residueIndex + 1,
        chain_id: chainId,
        x: caX + position.dx,
        y: caY + position.dy,
        z: z + position.dz,
      })
      if (position.name === 'CA') cAlphaByResidue.push(serial)
    }

    // Peptide bond from the previous residue's carbonyl carbon to this N.
    if (previousCarbon.length > 0) {
      bonds.push({ atom_a: previousCarbon[0], atom_b: residueAtoms[0], order: 1 })
    }
    bonds.push({ atom_a: residueAtoms[0], atom_b: residueAtoms[1], order: 1 })
    bonds.push({ atom_a: residueAtoms[1], atom_b: residueAtoms[2], order: 1 })
    bonds.push({ atom_a: residueAtoms[2], atom_b: residueAtoms[3], order: 1 })
    previousCarbon[0] = residueAtoms[2]

    // A few side-chain atoms (CA-CB stub) for visual variety.
    if (residueIndex % 3 === 0) {
      serial += 1
      atoms.push({
        index: serial,
        element: 'C',
        atom_name: 'CB',
        residue_name: RESIDUE_NAMES[residueIndex],
        residue_index: residueIndex + 1,
        chain_id: chainId,
        x: caX + 1.1,
        y: caY - 0.4,
        z: z + 0.3,
      })
      bonds.push({ atom_a: cAlphaByResidue[residueIndex], atom_b: serial, order: 1 })
      residueAtoms.push(serial)
    }

    residues.push({
      index: residueIndex + 1,
      name: RESIDUE_NAMES[residueIndex],
      atom_indices: residueAtoms,
    })
  }

  return {
    id: 'fixture-mini-p53-helix',
    name: 'p53 N-terminal helix (synthetic fixture)',
    kind: 'protein',
    organism: 'Homo sapiens',
    description:
      'Synthetic alpha-helix-like trace over the N-terminal residues of TP53. Development fixture, not a real molecule.',
    chains: [{ id: chainId, residues }],
    atoms,
    bonds,
    metadata: { source: 'fixture', format: 'synthetic-helix' },
  }
}

/** The raw fixture record, routed through the production normalizer. */
export const P53_HELIX_STRUCTURE_FIXTURE: MolecularStructure = toStructure(buildRawFixture())

/** A deliberately empty structure fixture for the empty-state tests/demo. */
export const EMPTY_STRUCTURE_FIXTURE: MolecularStructure = toStructure({
  id: 'fixture-empty',
  name: 'Empty structure',
  kind: 'protein',
  chains: [],
  atoms: [],
  bonds: [],
})
