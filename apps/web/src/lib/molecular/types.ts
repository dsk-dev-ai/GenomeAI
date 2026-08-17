/**
 * TypeScript types for the Molecular Structure Viewer (Phase 6.12).
 *
 * ## Coordinate conventions
 *
 * Atoms carry **Cartesian coordinates in angstroms**. Atom serials, residue
 * numbers, and bond endpoints are **one-based**, mirroring the 1-based
 * residue convention of the Phase 6.5 Protein Viewer. A residue's
 * `atomIndices` refer to 1-based atom serials; a bond's `atomA`/`atomB`
 * refer to the same serials.
 *
 * ## Data boundary
 *
 * These types are the canonical structure model the viewer renders. They are
 * deliberately independent of any particular file format or backend: the
 * loader boundary (`lib/molecular/api.ts`) normalizes whatever a future
 * source returns into this model, so swapping data sources never touches the
 * viewer or its representations.
 */

/** Free-form metadata carried by a structure without extra types. */
export type StructureMetadata = Record<string, string | number | boolean>

/** Molecule class used for default presentation. */
export type StructureKind = 'protein' | 'nucleic-acid' | 'other'

/** A single atom with its 3D position and residue context. */
export interface StructureAtom {
  /** 1-based atom serial; bonds and residues reference this. */
  index: number
  /** Chemical element symbol, uppercase (e.g. `C`, `N`, `O`, `S`). */
  element: string
  /** Cartesian coordinates in angstroms. */
  x: number
  y: number
  z: number
  /** 1-based residue number within the chain. */
  residueIndex: number
  /** Chain identifier (opaque string). */
  chainId: string
  /** Residue / group name, e.g. `ALA`. */
  residueName?: string
  /** Atom name, e.g. `CA`, `N`, `C`, `O`. */
  atomName?: string
}

/** A covalent bond between two atoms. */
export interface StructureBond {
  /** 1-based serial of the first atom. */
  atomA: number
  /** 1-based serial of the second atom. */
  atomB: number
  /** Bond order (single/double/triple); defaults to `1`. */
  order?: number
}

/** A residue (or other group) belonging to a chain. */
export interface StructureResidue {
  /** 1-based residue number within the chain. */
  index: number
  /** Residue / group name, e.g. `ALA`. */
  name?: string
  /** 1-based atom serials belonging to this residue. */
  atomIndices: number[]
}

/** A polymer chain made of ordered residues. */
export interface StructureChain {
  /** Chain identifier (opaque string). */
  id: string
  /** Residues in chain order. */
  residues: StructureResidue[]
}

/** The canonical molecular structure model rendered by the viewer. */
export interface MolecularStructure {
  /** Stable structure identifier (e.g. a PDB accession or future API id). */
  id: string
  /** Molecule name, e.g. `p53 DNA-binding domain`. */
  name?: string
  /** Molecule class used for default presentation. */
  kind?: StructureKind
  /** Organism, when known. */
  organism?: string
  /** Free-text description / function. */
  description?: string
  /** Polymer chains in structure order. */
  chains: StructureChain[]
  /** All atoms. */
  atoms: StructureAtom[]
  /** Covalent bonds, when available. */
  bonds: StructureBond[]
  /** Optional free-form metadata. */
  metadata?: StructureMetadata
}
