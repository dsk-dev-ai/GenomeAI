/**
 * Protein viewport construction and navigation (Phase 6.5).
 *
 * A protein viewport is a one-based-inclusive window over residues
 * `start..end` with `bounds.length` carrying the full protein length. The
 * pan/zoom/clamp math is **shared** with the Genome Browser
 * (`lib/genome/viewport.ts`) via the structural `IntervalWindow` shape, so
 * protein navigation cannot drift from genomic navigation. Pure functions.
 */

import { PAN_FRACTION, panViewport, viewportBaseCount, zoomViewport } from '@/lib/genome/viewport'

import type { ProteinViewport } from './types'

/** Number of residues shown in the opening window of a protein. */
export const PROTEIN_DEFAULT_WINDOW = 100

/** Minimum viewport width in residues (maximum zoom-in). */
export const MIN_VIEWPORT_RESIDUES = 1

/** A window over the full protein (`1..length`). */
export function wholeProteinViewport(length: number): ProteinViewport {
  const n = Math.max(1, Math.floor(length))
  return { start: 1, end: n, bounds: { length: n } }
}

/**
 * Opening window for a protein: the first `defaultWindow` residues, clamped
 * to the protein length. Guarantees the opening view is readable even for
 * very long proteins.
 */
export function initialProteinViewport(
  length: number,
  defaultWindow: number = PROTEIN_DEFAULT_WINDOW,
): ProteinViewport {
  const n = Math.max(1, Math.floor(length))
  const size = Math.max(MIN_VIEWPORT_RESIDUES, Math.min(Math.floor(defaultWindow), n))
  return { start: 1, end: size, bounds: { length: n } }
}

/** Full protein length used for clamping (from bounds, else the window end). */
export function proteinViewportLength(viewport: ProteinViewport): number {
  return viewport.bounds?.length ?? viewport.end
}

/** Number of visible residues in the window. */
export function proteinViewportSpan(viewport: ProteinViewport): number {
  return viewportBaseCount(viewport)
}

/** Pans by `delta` residues (positive = right), clamped to `1..length`. */
export function panProteinViewport(viewport: ProteinViewport, delta: number): ProteinViewport {
  return panViewport(viewport, delta)
}

/** Zooms around the window centre by `factor`, clamped to `1..length`. */
export function zoomProteinViewport(viewport: ProteinViewport, factor: number): ProteinViewport {
  return zoomViewport(viewport, factor)
}

/** Pans by a fraction of the current window (like the Genome Browser). */
export function panFraction(viewport: ProteinViewport, sign: 1 | -1): number {
  return (
    sign * Math.max(MIN_VIEWPORT_RESIDUES, Math.round(proteinViewportSpan(viewport) * PAN_FRACTION))
  )
}

/** Jumps to an explicit residue window, clamped to `1..length`. */
export function navigateProteinViewport(
  viewport: ProteinViewport,
  start: number,
  end: number,
): ProteinViewport {
  const length = proteinViewportLength(viewport)
  const lo = Math.max(MIN_VIEWPORT_RESIDUES, Math.floor(start))
  const hi = Math.min(length, Math.floor(end))
  if (lo > hi) return viewport
  return { ...viewport, start: lo, end: hi, bounds: viewport.bounds }
}

export type ProteinRegionResult =
  | { ok: true; start: number; end: number }
  | { ok: false; error: string }

/**
 * Parses a residue window from user input: a single position (`42`) or a
 * range (`42-80`). Values are clamped to the protein length; malformed input
 * returns a typed error.
 */
export function parseProteinRegion(input: string, length: number): ProteinRegionResult {
  const trimmed = input.trim()
  if (trimmed.length === 0) {
    return { ok: false, error: 'Enter a residue position or range, e.g. 42 or 42-80.' }
  }

  const parts = trimmed.split('-')
  if (parts.length === 1) {
    const value = Number(parts[0])
    if (!Number.isFinite(value) || value < 1) {
      return { ok: false, error: 'Residue positions are integers >= 1.' }
    }
    const start = Math.min(Math.floor(value), length)
    return { ok: true, start, end: start }
  }

  if (parts.length === 2) {
    const startValue = Number(parts[0])
    const endValue = Number(parts[1])
    if (!Number.isFinite(startValue) || !Number.isFinite(endValue)) {
      return { ok: false, error: 'Residue positions must be integers.' }
    }
    if (startValue < 1 || endValue < startValue) {
      return { ok: false, error: 'Range must satisfy 1 <= start <= end.' }
    }
    const start = Math.min(Math.floor(startValue), length)
    const end = Math.min(Math.floor(endValue), length)
    if (start > end) return { ok: false, error: 'Range falls outside the protein length.' }
    return { ok: true, start, end }
  }

  return { ok: false, error: 'Use a single position (42) or a range (42-80).' }
}
