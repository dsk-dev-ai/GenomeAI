/**
 * Protein sequence utilities (Phase 6.5).
 *
 * Pure functions over the amino-acid sequence string. Residue indices are
 * **one-based** (see `lib/protein/types.ts`): residue `1` is the first
 * character of the sequence. Nothing here touches the DOM or network, so
 * every rule is unit-testable.
 */

import type { ProteinResidue } from './types'

/** The 20 canonical amino-acid one-letter codes. */
export const AMINO_ACIDS = [
  'A',
  'C',
  'D',
  'E',
  'F',
  'G',
  'H',
  'I',
  'K',
  'L',
  'M',
  'N',
  'P',
  'Q',
  'R',
  'S',
  'T',
  'V',
  'W',
  'Y',
] as const

const AMINO_ACID_SET = new Set<string>(AMINO_ACIDS)

/** Length of the sequence in residues. */
export function sequenceLength(sequence: string): number {
  return sequence.length
}

/**
 * True when the sequence is non-empty and every residue is a canonical
 * amino-acid letter. Ambiguous/unknown codes (`X`, `B`, `Z`, `U`, `*`)
 * are rejected so invalid records surface early at the adapter boundary.
 */
export function isValidSequence(sequence: string): boolean {
  if (sequence.length === 0) return false
  for (let i = 0; i < sequence.length; i += 1) {
    const code = sequence.charAt(i).toUpperCase()
    if (!AMINO_ACID_SET.has(code)) return false
  }
  return true
}

/** One-letter amino-acid code at a 1-based residue index (uppercased). */
export function aminoAcidAt(sequence: string, index: number): string | undefined {
  if (!Number.isSafeInteger(index) || index < 1 || index > sequence.length) return undefined
  return sequence.charAt(index - 1).toUpperCase()
}

/** Residue record at a 1-based index, or `undefined` out of range. */
export function residueAt(sequence: string, index: number): ProteinResidue | undefined {
  const aminoAcid = aminoAcidAt(sequence, index)
  return aminoAcid === undefined ? undefined : { index, aminoAcid }
}

/**
 * 1-based inclusive slice of the sequence (`start..end`). Out-of-range
 * indices are clamped; invalid windows (`start > end`) return the empty
 * string. A single residue at `start === end` returns one letter.
 */
export function sequenceSlice(sequence: string, start: number, end: number): string {
  const lo = Math.max(1, Math.floor(start))
  const hi = Math.min(sequence.length, Math.floor(end))
  if (lo > hi) return ''
  return sequence.slice(lo - 1, hi)
}

/** True when `index` is a valid 1-based residue of `sequence`. */
export function isValidResidueIndex(sequence: string, index: number): boolean {
  return Number.isSafeInteger(index) && index >= 1 && index <= sequence.length
}

/**
 * Residue records for the (clipped) window `start..end`, in order. Only
 * residues inside the sequence are returned; a window fully outside it
 * yields `[]`. Deterministic and bounded by the window size.
 */
export function residuesInWindow(sequence: string, start: number, end: number): ProteinResidue[] {
  const lo = Math.max(1, Math.floor(start))
  const hi = Math.min(sequence.length, Math.floor(end))
  if (lo > hi) return []

  const residues: ProteinResidue[] = []
  for (let index = lo; index <= hi; index += 1) {
    residues.push({ index, aminoAcid: sequence.charAt(index - 1).toUpperCase() })
  }
  return residues
}
