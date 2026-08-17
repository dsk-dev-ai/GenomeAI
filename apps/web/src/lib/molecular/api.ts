/**
 * Molecular structure data adapter (Phase 6.12).
 *
 * Documents the future GenomeAI structure contract and normalizes raw wire
 * records into the canonical `MolecularStructure` model:
 *
 *     GET /structures/{structure_id}
 *
 * The backend does **not yet expose any molecular structure endpoint**. This
 * adapter defines the normalized shape a future source is expected to return
 * and provides `toStructure` so a real endpoint can be wired in without
 * touching the viewer. Until then the demo uses the clearly isolated
 * development fixture in `lib/molecular/molecular.fixtures.ts`, routed through
 * the same normalizer as production. See `docs/visualization/molecular-structure.md`.
 */

import { API_BASE_URL, GenomeApiError, asNumber, asString } from '@/lib/genome/api'
import type {
  MolecularStructure,
  StructureAtom,
  StructureBond,
  StructureChain,
  StructureKind,
  StructureResidue,
} from './types'
import { firstStructureError } from './validate'

/** Raw record shape a future `GET /structures/{id}` endpoint would return. */
export interface RawStructureRecord {
  id?: unknown
  name?: unknown
  molecule_name?: unknown
  kind?: unknown
  molecule_type?: unknown
  organism?: unknown
  description?: unknown
  chains?: unknown
  atoms?: unknown
  bonds?: unknown
  metadata?: unknown
  [key: string]: unknown
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asKind(value: unknown): StructureKind | undefined {
  return value === 'protein' || value === 'nucleic-acid' || value === 'other' ? value : undefined
}

function toAtom(value: unknown): StructureAtom | undefined {
  if (!isObject(value)) return undefined
  const index = asNumber(value.index) ?? asNumber(value.serial)
  const x = asNumber(value.x) ?? asNumber(value.position_x)
  const y = asNumber(value.y) ?? asNumber(value.position_y)
  const z = asNumber(value.z) ?? asNumber(value.position_z)
  const residueIndex =
    asNumber(value.residue_index) ?? asNumber(value.residue_seq_number) ?? asNumber(value.residue)
  const chainId = asString(value.chain_id) ?? asString(value.chain)
  const element = (asString(value.element) ?? asString(value.element_symbol) ?? '').toUpperCase()
  if (index === undefined || x === undefined || y === undefined || z === undefined) {
    return undefined
  }
  return {
    index,
    element,
    x,
    y,
    z,
    residueIndex: residueIndex ?? 0,
    chainId: chainId ?? '',
    ...(asString(value.residue_name) !== undefined
      ? { residueName: asString(value.residue_name) }
      : {}),
    ...(asString(value.atom_name) !== undefined ? { atomName: asString(value.atom_name) } : {}),
  }
}

function toBond(value: unknown): StructureBond | undefined {
  if (!isObject(value)) return undefined
  const atomA = asNumber(value.atom_a) ?? asNumber(value.atom1)
  const atomB = asNumber(value.atom_b) ?? asNumber(value.atom2)
  const order = asNumber(value.order)
  if (atomA === undefined || atomB === undefined) return undefined
  return { atomA, atomB, ...(order !== undefined ? { order } : {}) }
}

function toResidue(value: unknown): StructureResidue | undefined {
  if (!isObject(value)) return undefined
  const index = asNumber(value.index) ?? asNumber(value.residue_number)
  const atomIndices = Array.isArray(value.atom_indices)
    ? value.atom_indices
        .map((entry: unknown) => (typeof entry === 'number' ? entry : asNumber(entry)))
        .filter((entry: number | undefined): entry is number => entry !== undefined)
    : []
  if (index === undefined) return undefined
  return {
    index,
    ...(asString(value.name) !== undefined ? { name: asString(value.name) } : {}),
    atomIndices,
  }
}

function toChain(value: unknown): StructureChain | undefined {
  if (!isObject(value)) return undefined
  const id = asString(value.id) ?? asString(value.chain_id)
  const residues = Array.isArray(value.residues)
    ? value.residues
        .map(toResidue)
        .filter((residue): residue is StructureResidue => residue !== undefined)
    : []
  if (id === undefined) return undefined
  return { id, residues }
}

function toMetadata(value: unknown): Record<string, string | number | boolean> | undefined {
  if (!isObject(value)) return undefined
  const entries = Object.entries(value).filter(
    (entry): entry is [string, string | number | boolean] => {
      const [, field] = entry
      return typeof field === 'string' || typeof field === 'number' || typeof field === 'boolean'
    },
  )
  return entries.length > 0 ? Object.fromEntries(entries) : undefined
}

/**
 * Normalizes a raw structure record into the canonical `MolecularStructure`.
 * Records that are not objects (or lack coordinates) are dropped; the result
 * should be validated with `validateStructure` before rendering.
 */
export function toStructure(item: RawStructureRecord): MolecularStructure {
  const id = asString(item.id) ?? asString(item.structure_id) ?? ''
  const atoms = Array.isArray(item.atoms)
    ? item.atoms.map(toAtom).filter((atom): atom is StructureAtom => atom !== undefined)
    : []
  const bonds = Array.isArray(item.bonds)
    ? item.bonds.map(toBond).filter((bond): bond is StructureBond => bond !== undefined)
    : []
  const chains = Array.isArray(item.chains)
    ? item.chains.map(toChain).filter((chain): chain is StructureChain => chain !== undefined)
    : []

  const name = asString(item.name) ?? asString(item.molecule_name)
  const kind = asKind(item.kind) ?? asKind(item.molecule_type)
  const organism = asString(item.organism)
  const description = asString(item.description)
  const metadata = toMetadata(item.metadata)

  return {
    id,
    ...(name !== undefined ? { name } : {}),
    ...(kind !== undefined ? { kind } : {}),
    ...(organism !== undefined ? { organism } : {}),
    ...(description !== undefined ? { description } : {}),
    chains,
    atoms,
    bonds,
    ...(metadata !== undefined ? { metadata } : {}),
  }
}

/** True when a raw record could plausibly describe a structure. */
export function isStructureRecord(value: unknown): value is RawStructureRecord {
  return isObject(value)
}

/**
 * Fetches a single structure by id and normalizes it, reusing the caller's
 * `AbortSignal`. Only usable once the backend exposes `GET /structures/{id}`;
 * it throws a descriptive error otherwise.
 */
export async function fetchMolecularStructure(
  structureId: string,
  signal?: AbortSignal,
): Promise<MolecularStructure> {
  const response = await fetch(`${API_BASE_URL}/structures/${encodeURIComponent(structureId)}`, {
    headers: { 'Content-Type': 'application/json' },
    signal,
  })

  if (!response.ok) {
    throw new GenomeApiError(
      `GenomeAI API returned ${response.status} for structure ${structureId}`,
      response.status,
    )
  }

  const payload = (await response.json()) as RawStructureRecord | null
  if (!isStructureRecord(payload)) {
    throw new GenomeApiError(
      `GenomeAI API returned an invalid payload for structure ${structureId}`,
    )
  }

  const structure = toStructure(payload)
  const error = firstStructureError(structure)
  if (error !== null) {
    throw new GenomeApiError(
      `GenomeAI API returned an invalid structure for ${structureId}: ${error}`,
    )
  }
  return structure
}
