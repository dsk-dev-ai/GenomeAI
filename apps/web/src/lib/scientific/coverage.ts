/**
 * Coverage dataset validation, normalization, domains, and tooltips (Phase 6.8).
 *
 * Pure functions over `CoverageDataset`. Coverage bins follow the Phase 6.2
 * one-based inclusive coordinate conventions from `lib/genome/types.ts`
 * (`start >= 1`, `start <= end`, `length = end - start + 1`). The module
 * reuses those semantics instead of defining a parallel coordinate model.
 *
 * - `validateCoverageDataset` reports invalid bins (bad intervals or
 *   non-finite coverage).
 * - `normalizeCoverageDataset` builds a deterministic, render-ready dataset
 *   (invalid bins dropped, overlapping duplicate intervals deduped, bins
 *   ordered canonically by chromosome/start/end).
 * - `coverageChromosomes` and `coverageDomains` derive the x/y value domains.
 * - `coverageBinTooltip` maps a bin to the labelled tooltip rows.
 */

import type { CoverageBin, CoverageDataset } from './advancedTypes'
import { type PointTooltip, formatTooltipValue } from './tooltip'

export interface CoverageValidationResult {
  valid: boolean
  errors: string[]
}

function isValidIdentifier(value: string): boolean {
  return value.trim().length > 0
}

function isValidInterval(start: number, end: number): boolean {
  return Number.isInteger(start) && Number.isInteger(end) && start >= 1 && start <= end
}

/** Reports problems with a coverage dataset. Invalid bins have an empty
 * chromosome, a non-integer or inverted interval, or non-finite coverage. */
export function validateCoverageDataset(dataset: CoverageDataset): CoverageValidationResult {
  const errors: string[] = []
  if (!isValidIdentifier(dataset.id)) {
    errors.push('Dataset id must be a non-empty string.')
  }
  if (!isValidIdentifier(dataset.title)) {
    errors.push('Dataset title must be a non-empty string.')
  }
  dataset.bins.forEach((bin, index) => {
    if (!isValidIdentifier(bin.chromosome)) {
      errors.push(`Bin ${index}: chromosome must be a non-empty string.`)
    }
    if (!isValidInterval(bin.start, bin.end)) {
      errors.push(
        `Bin ${index}: interval must satisfy 1 <= start <= end (got ${bin.start}..${bin.end}).`,
      )
    }
    if (!Number.isFinite(bin.coverage)) {
      errors.push(`Bin ${index}: coverage must be a finite number.`)
    }
  })
  return { valid: errors.length === 0, errors }
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

/** Canonical interval key: chromosome + start + end. */
function intervalKey(bin: CoverageBin): string {
  return `${bin.chromosome}\u0000${bin.start}\u0000${bin.end}`
}

/**
 * Builds a deterministic, render-ready coverage dataset: invalid bins are
 * dropped, bins sharing a chromosome/start/end interval are deduped (first
 * wins), and bins are ordered canonically by chromosome, start, then end.
 * The result is always structurally valid and never shares mutable state
 * with the input.
 */
export function normalizeCoverageDataset(dataset: CoverageDataset): CoverageDataset {
  const seen = new Set<string>()
  const bins = dataset.bins
    .filter((bin) => {
      if (!isValidIdentifier(bin.chromosome)) return false
      if (!isValidInterval(bin.start, bin.end)) return false
      if (!Number.isFinite(bin.coverage)) return false
      const key = intervalKey(bin)
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .map(cloneBin)
    .sort((left, right) => {
      const byChromosome = compareText(left.chromosome, right.chromosome)
      if (byChromosome !== 0) return byChromosome
      if (left.start !== right.start) return left.start - right.start
      return left.end - right.end
    })

  return {
    id: dataset.id.trim().length > 0 ? dataset.id : 'unnamed-coverage',
    title: dataset.title.trim().length > 0 ? dataset.title : 'Unnamed coverage dataset',
    bins,
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}

function cloneBin(bin: CoverageBin): CoverageBin {
  return {
    ...bin,
    ...(bin.metadata !== undefined ? { metadata: { ...bin.metadata } } : {}),
  }
}

/** Whether the dataset holds at least one renderable bin. */
export function hasRenderableBins(dataset: CoverageDataset): boolean {
  return dataset.bins.length > 0
}

/**
 * The sorted, unique set of chromosomes present in the dataset. Drives the
 * coverage chart's interval axis; ordering is deterministic (code-unit).
 */
export function coverageChromosomes(dataset: CoverageDataset): string[] {
  const chromosomes = new Set<string>()
  for (const bin of dataset.bins) {
    if (bin.chromosome.trim().length > 0) chromosomes.add(bin.chromosome)
  }
  return [...chromosomes].sort(compareText)
}

export interface ValueDomain {
  min: number
  max: number
}

/**
 * The min/max coverage depth across all bins of a chromosome. Returns
 * `undefined` when the chromosome has no bins.
 */
export function coverageDomain(
  dataset: CoverageDataset,
  chromosome: string,
): ValueDomain | undefined {
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  let found = false
  for (const bin of dataset.bins) {
    if (bin.chromosome !== chromosome) continue
    if (bin.coverage < min) min = bin.coverage
    if (bin.coverage > max) max = bin.coverage
    found = true
  }
  return found ? { min, max } : undefined
}

/** The min start and max end across a chromosome's bins, or `undefined`. */
export function coverageExtent(
  dataset: CoverageDataset,
  chromosome: string,
): { start: number; end: number } | undefined {
  let start = Number.POSITIVE_INFINITY
  let end = Number.NEGATIVE_INFINITY
  let found = false
  for (const bin of dataset.bins) {
    if (bin.chromosome !== chromosome) continue
    if (bin.start < start) start = bin.start
    if (bin.end > end) end = bin.end
    found = true
  }
  return found ? { start, end } : undefined
}

/**
 * Builds the tooltip content for a coverage bin. The title is the
 * chromosome, the subtitle the interval, and the rows carry the coverage
 * depth plus any metadata fields.
 */
export function coverageBinTooltip(bin: CoverageBin): PointTooltip {
  const rows = [{ label: 'Coverage', value: formatTooltipValue(bin.coverage) }]
  if (bin.metadata !== undefined) {
    for (const [key, value] of Object.entries(bin.metadata)) {
      rows.push({ label: key, value: String(value) })
    }
  }
  return {
    title: bin.chromosome,
    subtitle: `${formatInterval(bin.start)}–${formatInterval(bin.end)}`,
    rows,
  }
}

function formatInterval(position: number): string {
  return position.toLocaleString('en-US')
}
