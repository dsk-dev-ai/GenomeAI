/**
 * Pure layout geometry for the Gene / Transcript viewer (Phase 6.3).
 *
 * All functions map one-based-inclusive genomic coordinates onto a pixel
 * canvas using the shared Genome Browser scale (`lib/genome/geometry.ts`), so
 * exon blocks, intron connectors, and the gene span stay aligned with any
 * Genome Browser axis built from the same viewport. Keeping the math here —
 * away from the React component — makes every rule unit-testable and keeps
 * the SVG renderer thin.
 */

import type { GeneExon, GeneTranscript } from './geneTranscript'
import { intervalToPixels } from './geometry'
import type { GenomeScale, PixelSpan, RenderedSpan } from './geometry'
import type { GenomeViewport } from './types'

export type { PixelSpan, RenderedSpan }
export { intervalToPixels }

/** Vertical stride used between transcript lanes. */
export const TRANSCRIPT_LANE_HEIGHT = 22

/** Vertical height reserved for the single gene lane. */
export const GENE_LANE_HEIGHT = 20

/** Height of an exon block within a transcript lane. */
export const EXON_HEIGHT = 8

/** Thickness (stroke-width) of the intron connector line. */
export const INTRON_WIDTH = 1.5

/** Vertical placement of a transcript lane within the viewer. */
export interface TranscriptLane {
  /** Index of the lane (0-based, in display order). */
  index: number
  /** Vertical offset (px) of the lane's centre line. */
  y: number
}

/**
 * Pixel geometry of a single exon block, clipped to the viewport. Exons
 * fully outside the viewport report `visible: false`.
 */
export function exonToPixels(
  scale: GenomeScale,
  viewport: GenomeViewport,
  exon: GeneExon,
): RenderedSpan {
  return intervalToPixels(scale, viewport, exon.start, exon.end)
}

/**
 * Pixel geometry of a transcript's intron connector (its full span). When a
 * transcript has exons the connector runs the full span with exon blocks
 * drawn on top; without exons it is the only structure drawn.
 */
export function transcriptToPixels(
  scale: GenomeScale,
  viewport: GenomeViewport,
  transcript: GeneTranscript,
): RenderedSpan {
  return intervalToPixels(scale, viewport, transcript.start, transcript.end)
}

/**
 * Vertical lane placement for a list of transcripts, in display order.
 * Each transcript occupies its own lane (index 0 at the top) so isoform
 * structure is never drawn on top of another transcript.
 */
export function layoutTranscriptLanes(transcripts: readonly GeneTranscript[]): TranscriptLane[] {
  return transcripts.map((_transcript, index) => ({
    index,
    y: GENE_LANE_HEIGHT + index * TRANSCRIPT_LANE_HEIGHT,
  }))
}

/** Total pixel height needed for the gene lane plus all transcript lanes. */
export function geneTranscriptHeight(transcriptCount: number): number {
  return GENE_LANE_HEIGHT + transcriptCount * TRANSCRIPT_LANE_HEIGHT
}

/** Pixel x of the gene lane's leading label region (left gutter). */
export const GENE_LABEL_X = 4

/** Pixel offset from the lane centre used to align labels above the row. */
export const LABEL_Y_OFFSET = -7
