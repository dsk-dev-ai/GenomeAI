/**
 * Structure validation (Phase 6.12).
 *
 * Pure validation over the canonical `MolecularStructure` model. It reports
 * structural issues that would break rendering or lie about the data:
 * non-finite / missing coordinates, broken atom serials, bonds or residue
 * references that point nowhere, self-bonds, and empty structures. The viewer
 * uses `isUsableStructure` to decide whether a loaded structure can render;
 * malformed records are still typed and testable rather than silently fixed.
 */

import type { MolecularStructure, StructureAtom, StructureBond } from './types'

/** A single validation finding. */
export interface StructureValidationIssue {
  /** Stable machine-readable code, e.g. `atom.non-finite-coordinates`. */
  code: string
  /** Human-readable description of the problem. */
  message: string
}

const MAX_ATOM_INDEX = 1_000_000

/** True when a value is a positive integer usable as an atom serial. */
function isPositiveInteger(value: number): boolean {
  return Number.isInteger(value) && value >= 1 && value <= MAX_ATOM_INDEX
}

function isFinitePoint(atom: StructureAtom): boolean {
  return Number.isFinite(atom.x) && Number.isFinite(atom.y) && Number.isFinite(atom.z)
}

function residueAtomIndices(structure: MolecularStructure): number[] {
  return structure.chains.flatMap((chain) =>
    chain.residues.flatMap((residue) => residue.atomIndices),
  )
}

/**
 * Validates a structure and returns every issue found. An empty array means
 * the structure is structurally consistent and renderable.
 */
export function validateStructure(structure: MolecularStructure): StructureValidationIssue[] {
  const issues: StructureValidationIssue[] = []

  if (structure.id.length === 0) {
    issues.push({ code: 'structure.missing-id', message: 'Structure has no identifier.' })
  }
  if (structure.atoms.length === 0) {
    issues.push({ code: 'structure.no-atoms', message: 'Structure has no atoms to render.' })
  }

  const atomByIndex = new Map<number, StructureAtom>()
  for (const atom of structure.atoms) {
    if (!isPositiveInteger(atom.index)) {
      issues.push({
        code: 'atom.invalid-index',
        message: `Atom has an invalid serial ${atom.index}.`,
      })
    } else if (atomByIndex.has(atom.index)) {
      issues.push({
        code: 'atom.duplicate-index',
        message: `Atom serial ${atom.index} appears more than once.`,
      })
    } else {
      atomByIndex.set(atom.index, atom)
    }
    if (!isFinitePoint(atom)) {
      issues.push({
        code: 'atom.non-finite-coordinates',
        message: `Atom ${atom.index} has a non-finite coordinate.`,
      })
    }
    if (!isPositiveInteger(atom.residueIndex)) {
      issues.push({
        code: 'atom.invalid-residue',
        message: `Atom ${atom.index} has an invalid residue number ${atom.residueIndex}.`,
      })
    }
    if (atom.element.length === 0) {
      issues.push({ code: 'atom.missing-element', message: `Atom ${atom.index} has no element.` })
    }
  }

  const seenBonds = new Set<string>()
  for (const bond of structure.bonds) {
    if (!atomByIndex.has(bond.atomA) || !atomByIndex.has(bond.atomB)) {
      issues.push({
        code: 'bond.dangling',
        message: `Bond ${bond.atomA}-${bond.atomB} references a missing atom.`,
      })
    }
    if (bond.atomA === bond.atomB) {
      issues.push({
        code: 'bond.self-loop',
        message: `Bond ${bond.atomA}-${bond.atomA} joins an atom to itself.`,
      })
    }
    const key =
      bond.atomA < bond.atomB ? `${bond.atomA}-${bond.atomB}` : `${bond.atomB}-${bond.atomA}`
    if (seenBonds.has(key)) {
      issues.push({
        code: 'bond.duplicate',
        message: `Bond ${key} appears more than once.`,
      })
    }
    seenBonds.add(key)
  }

  for (const chain of structure.chains) {
    if (chain.id.length === 0) {
      issues.push({ code: 'chain.missing-id', message: 'A chain has no identifier.' })
    }
    const residueNumbers = new Set<number>()
    for (const residue of chain.residues) {
      if (!isPositiveInteger(residue.index)) {
        issues.push({
          code: 'residue.invalid-index',
          message: `Chain ${chain.id || '?'} has a residue with an invalid number.`,
        })
      } else if (residueNumbers.has(residue.index)) {
        issues.push({
          code: 'residue.duplicate-index',
          message: `Chain ${chain.id || '?'} has residue ${residue.index} more than once.`,
        })
      }
      residueNumbers.add(residue.index)
      for (const atomIndex of residue.atomIndices) {
        if (!atomByIndex.has(atomIndex)) {
          issues.push({
            code: 'residue.dangling-atom',
            message: `Residue ${residue.index} of chain ${chain.id || '?'} references missing atom ${atomIndex}.`,
          })
        }
      }
    }
  }

  const referencedByResidues = new Set(residueAtomIndices(structure))
  for (const atom of structure.atoms) {
    if (!referencedByResidues.has(atom.index)) {
      issues.push({
        code: 'atom.unreferenced',
        message: `Atom ${atom.index} belongs to no residue.`,
      })
    }
  }

  return issues
}

/** True when a structure has no validation issues at all. */
export function isValidStructure(structure: MolecularStructure): boolean {
  return validateStructure(structure).length === 0
}

/**
 * True when a structure can actually be rendered: it must pass validation and
 * contain at least one atom. `empty` structures are handled by the data
 * lifecycle (`isEmpty`), not by rendering.
 */
export function isUsableStructure(structure: MolecularStructure): boolean {
  return structure.atoms.length > 0 && isValidStructure(structure)
}

/** The first issue's message, or `null` when the structure is valid. */
export function firstStructureError(structure: MolecularStructure): string | null {
  const issues = validateStructure(structure)
  return issues.length > 0 ? issues[0].message : null
}
