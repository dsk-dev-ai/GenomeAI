/**
 * Chromosome / contig identifier handling for the Genome Browser.
 *
 * Validation mirrors the backend regex used by Phase 5 coordinate search
 * (`apps/api/src/genomeai_api/search/coordinate_validation.py`): optional
 * `chr` prefix plus `1..22`, `X`, `Y`, `MT`, or `M`. The backend HTTP
 * boundary is permissive, so the browser validates client-side to deliver
 * clear, accessible errors before issuing a request.
 */

const CHROMOSOME_PATTERN = /^(?:chr)?([1-9][0-9]?|X|Y|MT|M)$/i

/**
 * Returns the canonical `chr…` form of a chromosome identifier (e.g.
 * `chr17`, `chrX`, `chrMT`), or `null` when the input is not a valid
 * autosome/sex/mitochondrial identifier.
 */
export function normalizeChromosome(input: string): string | null {
  const match = CHROMOSOME_PATTERN.exec(input.trim())
  if (!match?.length) return null
  return `chr${match[1].toUpperCase()}`
}

/** True when `input` describes a valid chromosome identifier. */
export function isValidChromosome(input: string): boolean {
  return normalizeChromosome(input) !== null
}
