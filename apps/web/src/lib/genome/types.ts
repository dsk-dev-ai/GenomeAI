/**
 * TypeScript types for the Genome Browser (Phase 6.2).
 *
 * ## Coordinate conventions
 *
 * All genomic coordinates used by the Genome Browser are **one-based and
 * inclusive** (Ensembl/NCBI style). A `start` of `1` refers to the first
 * base of the chromosome, and a feature spanning `start..end` covers
 * `length = end - start + 1` bases. This matches the inclusive
 * `start <= pos <= end` overlap semantics of GenomeAI's coordinate search
 * API (`POST /search/{domain}/coordinate`).
 *
 * The web client never silently mixes coordinate systems: the parser
 * enforces `start >= 1`, and the browser renders features/axis positions
 * derived from these same values. If a future data source supplies
 * zero-based (half-open) intervals, conversion must happen at the data
 * adapter boundary and be documented there.
 */

/** Identifier of an organism/genome build (e.g. `GRCh38.p14`). */
export type GenomeBuild = string

/** A reference genome the browser can navigate. */
export interface GenomeReference {
  /** Stable identifier, e.g. a genome record uuid. */
  id: string
  /** E.g. `GCA_000001405.29`. */
  accession: string
  /** Organism name, e.g. `Homo sapiens`. */
  organism: string
  /** Assembly / build version, e.g. `GRCh38.p14`. */
  assembly: GenomeBuild
}

/**
 * A one-based, inclusive genomic interval.
 *
 * `start` and `end` are base positions (>= 1). The invariant
 * `start <= end` is required; consumers must reject invalid intervals.
 */
export interface GenomicInterval {
  chromosome: string
  start: number
  end: number
}

/** The strand of a transcription unit where known. */
export type Strand = '+' | '-'

/** Optional domain-specific detail carried without plumbing extra types. */
export type FeatureMetadata = Record<string, string | number | boolean>

/** A genomic feature (gene, transcript, variant, ...). */
export interface GenomicFeature<Extra = FeatureMetadata> {
  id: string
  /** Feature class, e.g. `gene`, `transcript`, `variant`. */
  type: string
  chromosome: string
  /** 1-based inclusive start. */
  start: number
  /** 1-based inclusive end. */
  end: number
  strand?: Strand
  /** Short display name, e.g. `TP53`. */
  name?: string
  /** Optional domain-specific detail carried without plumbing extra types. */
  metadata?: Extra
}

/** Coordinates of a genomic variant (single position, 1-based). */
export interface VariantFeature<Extra = FeatureMetadata> extends GenomicFeature<Extra> {
  position: number
  ref?: string
  alt?: string
}

/** Known contig extents used to clamp navigation. */
export interface ContigBounds {
  /** Estimated/informed contig length, in 1-based inclusive bases. */
  length: number
}

/**
 * The currently visible window of the genome.
 *
 * `bounds` optionally carries contig-size knowledge used by navigation to
 * clamp pan/zoom. When bounds are unknown the viewport is treated as
 * open-ended on the high side.
 */
export interface GenomeViewport extends GenomicInterval {
  /** Optional known contig size used to clamp navigation. */
  bounds?: ContigBounds
}
