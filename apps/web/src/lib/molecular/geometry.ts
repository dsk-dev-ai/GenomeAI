/**
 * Pure structure geometry (Phase 6.12).
 *
 * Coordinate math, element presentation, and camera framing for the
 * Molecular Structure Viewer. Everything here is plain data — no Three.js,
 * no DOM, no WebGL — so it is fully unit-testable and shared by the viewer
 * and its tests.
 */

import type { MolecularStructure, StructureAtom } from './types'

/** A point in 3D space (angstroms). */
export interface Point3 {
  x: number
  y: number
  z: number
}

/** Presentation defaults for a chemical element. */
export interface ElementPresentation {
  /** CPK-style display colour as a hex string (no leading `#`). */
  color: string
  /** Van der Waals radius in angstroms (space-filling spheres). */
  vanDerWaalsRadius: number
  /** Ball-and-stick sphere radius in angstroms. */
  ballRadius: number
}

const ELEMENTS: Record<string, ElementPresentation> = {
  C: { color: '909090', vanDerWaalsRadius: 1.7, ballRadius: 0.35 },
  N: { color: '3050f8', vanDerWaalsRadius: 1.55, ballRadius: 0.35 },
  O: { color: 'ff0d0d', vanDerWaalsRadius: 1.52, ballRadius: 0.35 },
  S: { color: 'ffff30', vanDerWaalsRadius: 1.8, ballRadius: 0.4 },
  H: { color: 'ffffff', vanDerWaalsRadius: 1.2, ballRadius: 0.2 },
  P: { color: 'ff8000', vanDerWaalsRadius: 1.8, ballRadius: 0.4 },
  FE: { color: 'e06633', vanDerWaalsRadius: 1.8, ballRadius: 0.45 },
  ZN: { color: '7f80cc', vanDerWaalsRadius: 1.39, ballRadius: 0.45 },
  CL: { color: '1ff01f', vanDerWaalsRadius: 1.75, ballRadius: 0.4 },
  BR: { color: 'a62929', vanDerWaalsRadius: 1.85, ballRadius: 0.45 },
  CA: { color: '3dff3d', vanDerWaalsRadius: 1.8, ballRadius: 0.45 },
}

/** Default presentation used for any element without an entry. */
const DEFAULT_ELEMENT: ElementPresentation = {
  color: 'ff7f7f',
  vanDerWaalsRadius: 1.6,
  ballRadius: 0.35,
}

/** Atom serial → atom lookup for the geometry helpers. */
export type AtomIndex = Map<number, StructureAtom>

export function atomIndex(atoms: StructureAtom[]): AtomIndex {
  return new Map(atoms.map((atom) => [atom.index, atom]))
}

/** Presentation defaults for an element symbol (uppercase, unknown-safe). */
export function elementPresentation(element: string): ElementPresentation {
  return ELEMENTS[element.toUpperCase()] ?? DEFAULT_ELEMENT
}

/** Display colour (hex, no `#`) for an element symbol. */
export function elementColor(element: string): string {
  return elementPresentation(element).color
}

/** Bounding-box span of a set of atoms, or `undefined` when empty. */
export function structureBounds(atoms: StructureAtom[]): { min: Point3; max: Point3 } | undefined {
  if (atoms.length === 0) return undefined
  const min = {
    x: Number.POSITIVE_INFINITY,
    y: Number.POSITIVE_INFINITY,
    z: Number.POSITIVE_INFINITY,
  }
  const max = {
    x: Number.NEGATIVE_INFINITY,
    y: Number.NEGATIVE_INFINITY,
    z: Number.NEGATIVE_INFINITY,
  }
  for (const atom of atoms) {
    min.x = Math.min(min.x, atom.x)
    min.y = Math.min(min.y, atom.y)
    min.z = Math.min(min.z, atom.z)
    max.x = Math.max(max.x, atom.x)
    max.y = Math.max(max.y, atom.y)
    max.z = Math.max(max.z, atom.z)
  }
  return { min, max }
}

/** Centroid (mean) of all atoms, or `{0,0,0}` when empty. */
export function structureCentroid(atoms: StructureAtom[]): Point3 {
  if (atoms.length === 0) return { x: 0, y: 0, z: 0 }
  let x = 0
  let y = 0
  let z = 0
  for (const atom of atoms) {
    x += atom.x
    y += atom.y
    z += atom.z
  }
  const count = atoms.length
  return { x: x / count, y: y / count, z: z / count }
}

/** Largest distance from the centroid to any atom (angstroms). */
export function structureRadius(atoms: StructureAtom[], centroid: Point3): number {
  let radius = 0
  for (const atom of atoms) {
    const dx = atom.x - centroid.x
    const dy = atom.y - centroid.y
    const dz = atom.z - centroid.z
    radius = Math.max(radius, Math.sqrt(dx * dx + dy * dy + dz * dz))
  }
  return radius
}

/** Camera framing for a structure: the point to look at and its radius. */
export function cameraFocusForStructure(structure: MolecularStructure): {
  target: Point3
  radius: number
} {
  const centroid = structureCentroid(structure.atoms)
  return { target: centroid, radius: Math.max(structureRadius(structure.atoms, centroid), 1) }
}

/**
 * Backbone trace points per chain, in residue order. Uses the C-alpha atom of
 * each residue when present, otherwise the first atom of the residue — the
 * simplest meaningful spline backbone for the cartoon representation.
 */
export function backboneTrace(
  structure: MolecularStructure,
  atoms: StructureAtom[] = structure.atoms,
): Map<string, Point3[]> {
  const byChain = new Map<string, Point3[]>()
  const byIndex = atomIndex(atoms)
  for (const chain of structure.chains) {
    const points: Point3[] = []
    for (const residue of chain.residues) {
      const residueAtoms = residue.atomIndices
        .map((serial) => byIndex.get(serial))
        .filter((atom): atom is StructureAtom => atom !== undefined)
      const backbone =
        residueAtoms.find((atom) => (atom.atomName ?? '').toUpperCase() === 'CA') ?? residueAtoms[0]
      if (backbone !== undefined) {
        points.push({ x: backbone.x, y: backbone.y, z: backbone.z })
      }
    }
    if (points.length > 0) byChain.set(chain.id, points)
  }
  return byChain
}

/** Tally of atoms per element symbol, keyed by uppercase symbol. */
export function elementCounts(atoms: StructureAtom[]): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const atom of atoms) {
    const element = atom.element.toUpperCase()
    counts[element] = (counts[element] ?? 0) + 1
  }
  return counts
}

/** Human-readable summary of a structure for status lines and tests. */
export function structureSummary(structure: MolecularStructure): {
  name: string
  chains: number
  residues: number
  atoms: number
  bonds: number
  elements: Record<string, number>
  radius: number
  centroid: Point3
} {
  const residues = structure.chains.reduce((total, chain) => total + chain.residues.length, 0)
  return {
    name: structure.name ?? structure.id,
    chains: structure.chains.length,
    residues,
    atoms: structure.atoms.length,
    bonds: structure.bonds.length,
    elements: elementCounts(structure.atoms),
    radius: structureRadius(structure.atoms, structureCentroid(structure.atoms)),
    centroid: structureCentroid(structure.atoms),
  }
}
