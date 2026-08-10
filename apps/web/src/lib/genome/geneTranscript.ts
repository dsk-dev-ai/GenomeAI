/**
 * Gene / Transcript domain model (Phase 6.3).
 *
 * This module defines the typed biological model consumed by the gene /
 * transcript visualization and normalizes raw records from the Phase 5
 * coordinate-search API into that model. Coordinates follow the shared
 * Genome Browser convention: **one-based and inclusive** (see
 * `lib/genome/types.ts`), so `start..end` covers `end - start + 1` bases.
 *
 * The Phase 5 API exposes gene and transcript spans, strands, names, and a
 * transcript→gene relationship, but **does not yet expose exon structure**.
 * The model therefore carries `exons` on each transcript; the production
 * adapter fills it with `[]` and a clearly isolated development fixture
 * (`lib/genome/geneTranscript.fixtures.ts`) supplies exon structure so the
 * visualization can be developed and tested. See `geneTranscript.md` and the
 * adapter module for the exact boundary.
 */

import type { RawSearchItem } from './api'
import type { Strand } from './types'

/** A single exon (coding or UTR segment) of a transcript, 1-based inclusive. */
export interface GeneExon {
  /** Stable identifier where the source provides one. */
  id?: string
  /** 1-based inclusive start. */
  start: number
  /** 1-based inclusive end. */
  end: number
  /** Position of the exon within the transcript (1 = first transcribed). */
  rank?: number
}

/** One transcript (isoform) belonging to a gene. */
export interface GeneTranscript {
  /** Stable identifier (may be a search item id or accession). */
  id: string
  /** Short display name, e.g. `TP53-201` or `ENST00000269305`. */
  name: string
  chromosome: string
  /** 1-based inclusive start. */
  start: number
  /** 1-based inclusive end. */
  end: number
  strand: Strand
  /** Identifier of the owning gene when the source provides one. */
  geneId?: string
  /** Source accession, e.g. `ENST00000269305`. */
  transcriptId?: string
  /** e.g. `protein_coding`. */
  transcriptType?: string
  /** Exon blocks; empty when the source does not expose exon structure. */
  exons: GeneExon[]
}

/** A gene together with the transcripts that belong to it. */
export interface Gene {
  /** Stable identifier (may be a search item id or Ensembl id). */
  id: string
  /** Short display symbol, e.g. `TP53`. */
  symbol: string
  chromosome: string
  /** 1-based inclusive start. */
  start: number
  /** 1-based inclusive end. */
  end: number
  strand: Strand
  /** Source accession, e.g. `ENSG00000141510`. */
  geneId?: string
  /** e.g. `protein_coding`. */
  biotype?: string
  /** Transcripts ordered for display (see `sortTranscripts`). */
  transcripts: GeneTranscript[]
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

function asNumber(value: unknown): number | undefined {
  return typeof value === 'number' ? value : undefined
}

function idOf(value: unknown): string {
  if (typeof value === 'string' && value.length > 0) return value
  if (typeof value === 'object' && value !== null && 'id' in value) {
    return idOf((value as { id: unknown }).id)
  }
  return ''
}

function strandOf(value: unknown): Strand | undefined {
  return value === '+' || value === '-' ? value : undefined
}

/** True when `exon` carries a usable one-based inclusive span. */
export function isValidExon(exon: GeneExon): boolean {
  return (
    Number.isSafeInteger(exon.start) &&
    Number.isSafeInteger(exon.end) &&
    exon.start >= 1 &&
    exon.end >= exon.start
  )
}

/** True when `transcript` carries a usable genomic span. */
export function isValidTranscript(transcript: GeneTranscript): boolean {
  return (
    transcript.chromosome.length > 0 &&
    Number.isSafeInteger(transcript.start) &&
    Number.isSafeInteger(transcript.end) &&
    transcript.start >= 1 &&
    transcript.end >= transcript.start
  )
}

/** True when `gene` carries a usable genomic span. */
export function isValidGene(gene: Gene): boolean {
  return (
    gene.chromosome.length > 0 &&
    Number.isSafeInteger(gene.start) &&
    Number.isSafeInteger(gene.end) &&
    gene.start >= 1 &&
    gene.end >= gene.start
  )
}

/** Normalizes a raw exon record (used by fixtures and future API layers). */
export function toExon(item: RawSearchItem): GeneExon {
  const start = asNumber(item.start)
  const end = asNumber(item.end)
  const rank = asNumber(item.rank)
  const id = idOf(item)
  return {
    ...(id ? { id } : {}),
    ...(rank !== undefined ? { rank } : {}),
    start: start ?? 0,
    end: end ?? 0,
  }
}

/** Normalizes a raw transcript record from the coordinate-search API. */
export function toTranscript(item: RawSearchItem): GeneTranscript {
  const start = asNumber(item.start_position)
  const end = asNumber(item.end_position)
  const chromosome = asString(item.chromosome)
  const strand = strandOf(item.strand)
  const exonsRaw = Array.isArray(item.exons) ? (item.exons as unknown[]) : []
  return {
    id: idOf(item.id) || asString(item.transcript_id) || '',
    name: asString(item.transcript_name) || asString(item.transcript_id) || '',
    chromosome: chromosome ?? '',
    start: start ?? 0,
    end: end ?? 0,
    strand: strand ?? '+',
    ...(asString(item.gene_id) !== undefined ? { geneId: asString(item.gene_id) } : {}),
    ...(asString(item.transcript_id) !== undefined
      ? { transcriptId: asString(item.transcript_id) }
      : {}),
    ...(asString(item.transcript_type) !== undefined
      ? { transcriptType: asString(item.transcript_type) }
      : {}),
    exons: exonsRaw
      .filter((value): value is RawSearchItem => typeof value === 'object' && value !== null)
      .map(toExon)
      .filter(isValidExon),
  }
}

/** Normalizes a raw gene record from the coordinate-search API. */
export function toGene(item: RawSearchItem): Gene {
  const start = asNumber(item.start_position)
  const end = asNumber(item.end_position)
  const chromosome = asString(item.chromosome)
  const strand = strandOf(item.strand)
  return {
    id: idOf(item.id) || asString(item.gene_id) || '',
    symbol: asString(item.gene_name) || asString(item.gene_id) || '',
    chromosome: chromosome ?? '',
    start: start ?? 0,
    end: end ?? 0,
    strand: strand ?? '+',
    ...(asString(item.gene_id) !== undefined ? { geneId: asString(item.gene_id) } : {}),
    ...(asString(item.biotype) !== undefined ? { biotype: asString(item.biotype) } : {}),
    transcripts: [],
  }
}

/**
 * Orders transcripts for stable display: by genomic start, then end, then
 * id. The order is deterministic regardless of API result order.
 */
export function sortTranscripts(transcripts: readonly GeneTranscript[]): GeneTranscript[] {
  return [...transcripts].sort(
    (a, b) =>
      a.start - b.start ||
      a.end - b.end ||
      a.name.localeCompare(b.name) ||
      a.id.localeCompare(b.id),
  )
}

/**
 * Assigns transcripts to their owning gene.
 *
 * A transcript is placed on a gene when:
 * 1. the transcript explicitly references the gene — matching either the gene's
 *    search-record id or its accession (`gene.geneId`), or
 * 2. the transcript has no explicit gene link (fallback) and is on the same
 *    chromosome with its span contained within the gene span.
 *
 * A transcript that carries a gene link to a *different* gene is never
 * assigned by coordinate containment, so it is dropped rather than
 * mis-assigned. The returned genes are filtered to those with usable spans
 * and receive transcripts sorted for display.
 */
export function groupTranscriptsByGene(
  genes: readonly Gene[],
  transcripts: readonly GeneTranscript[],
): Gene[] {
  const result: Gene[] = []
  for (const gene of genes) {
    if (!isValidGene(gene)) continue
    const owned: GeneTranscript[] = []
    for (const transcript of transcripts) {
      if (!isValidTranscript(transcript)) continue
      const geneIds = [gene.id, gene.geneId].filter((value): value is string => value !== undefined)
      const explicit = transcript.geneId !== undefined && geneIds.includes(transcript.geneId)
      const contained =
        transcript.geneId === undefined &&
        transcript.chromosome === gene.chromosome &&
        transcript.start >= gene.start &&
        transcript.end <= gene.end
      if (explicit || contained) owned.push(transcript)
    }
    result.push({ ...gene, transcripts: sortTranscripts(owned) })
  }
  return result
}
