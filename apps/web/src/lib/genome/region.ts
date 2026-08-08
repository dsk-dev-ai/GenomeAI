/**
 * Genome region parsing (Phase 6.2).
 *
 * The browser accepts a human-friendly region such as:
 *
 *     chr1:100000-200000
 *
 * Chromosomes follow the shared chromosome patterns (`lib/genome/chromosome.ts`),
 * and coordinates are **one-based and inclusive** (see `lib/genome/types.ts`).
 *
 * Only a single region syntax is accepted here; expressive query-language
 * concerns belong to Phase 5.8's query DSL.
 */

import { normalizeChromosome } from './chromosome'
import type { GenomicInterval } from './types'

/** Normalized parser error codes; stable identifiers for tests and UI. */
export type RegionErrorCode =
  | 'malformed'
  | 'invalid_chromosome'
  | 'invalid_start'
  | 'invalid_end'
  | 'negative_start'
  | 'negative_end'
  | 'start_after_end'

export interface RegionValidationError {
  code: RegionErrorCode
  message: string
}

export type RegionParseResult =
  | { ok: true; interval: GenomicInterval }
  | { ok: false; error: RegionValidationError }

const REGION_PATTERN = /^([^:\s]+)\s*:\s*(-?\d+)\s*-\s*(-?\d+)\s*$/i

function isDigits(value: string): boolean {
  return /^\d+$/.test(value)
}

function coordinateError(
  value: string,
  negativeCode: RegionErrorCode,
  invalidCode: RegionErrorCode,
  label: string,
): RegionValidationError {
  const code = value.startsWith('-') ? negativeCode : invalidCode
  const message =
    code === negativeCode
      ? `${label} coordinate must not be negative.`
      : `'${value}' is not a valid ${label} coordinate.`
  return { code, message }
}

/**
 * Parses a single region string (`chr1:100000-200000`) into a validated
 * one-based `GenomicInterval`.
 *
 * - chromosome must match the shared backend chromosome pattern
 * - start/end must be present, non-negative integers
 * - start >= 1 and end >= 1 (one-based coordinates)
 * - start <= end
 */
export function parseGenomeRegion(input: string): RegionParseResult {
  const match = REGION_PATTERN.exec(input.trim())
  if (!match) {
    return {
      ok: false,
      error: { code: 'malformed', message: 'Region must look like chr1:100000-200000.' },
    }
  }

  const rawChromosome = match[1].trim()
  const rawStart = match[2]
  const rawEnd = match[3]

  const chromosome = normalizeChromosome(rawChromosome)
  if (!chromosome) {
    return {
      ok: false,
      error: {
        code: 'invalid_chromosome',
        message: `'${rawChromosome}' is not a valid chromosome (e.g. chr1, chrX, chrMT).`,
      },
    }
  }

  if (!isDigits(rawStart)) {
    return {
      ok: false,
      error: coordinateError(rawStart, 'negative_start', 'invalid_start', 'Start'),
    }
  }

  if (!isDigits(rawEnd)) {
    return {
      ok: false,
      error: coordinateError(rawEnd, 'negative_end', 'invalid_end', 'End'),
    }
  }

  const start = Number(rawStart)
  const end = Number(rawEnd)

  if (start < 1) {
    return {
      ok: false,
      error: {
        code: 'negative_start',
        message: 'Start coordinate must be at least 1 (one-based coordinates).',
      },
    }
  }
  if (end < 1) {
    return {
      ok: false,
      error: {
        code: 'negative_end',
        message: 'End coordinate must be at least 1 (one-based coordinates).',
      },
    }
  }
  if (start > end) {
    return {
      ok: false,
      error: {
        code: 'start_after_end',
        message: `Start (${start}) must not be greater than end (${end}).`,
      },
    }
  }

  return { ok: true, interval: { chromosome, start, end } }
}
