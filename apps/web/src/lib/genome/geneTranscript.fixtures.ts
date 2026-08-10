/**
 * Development fixture for Gene / Transcript visualization (Phase 6.3).
 *
 * The Phase 5 coordinate-search API exposes gene and transcript spans but
 * NOT exon structure. This module provides a small, clearly isolated, typed
 * fixture that mimics what a future backend exon endpoint would return, so
 * the visualization, its layout math, and its tests can be developed now.
 *
 * ## Boundary
 *
 * This is a **development fixture, not a real API**. It lives apart from
 * production adapters (`lib/genome/geneTranscriptApi.ts`), is never imported
 * by library code, and must be replaced by a real exon source as soon as the
 * backend exposes one. See `docs/visualization/gene-transcript.md`.
 */

import type { Gene, GeneTranscript } from './geneTranscript'

const STRAND_PLUS = '+' as const

/** A TP53-like transcript with a handful of exons (fixture coordinates). */
const tp53Transcripts: GeneTranscript[] = [
  {
    id: 'tx-tp53-201',
    name: 'TP53-201',
    chromosome: 'chr17',
    start: 7_665_901,
    end: 7_690_000,
    strand: STRAND_PLUS,
    geneId: 'gene-tp53',
    transcriptId: 'ENST00000269305',
    transcriptType: 'protein_coding',
    exons: [
      { id: 'exon-1', start: 7_665_901, end: 7_666_099, rank: 1 },
      { id: 'exon-2', start: 7_675_663, end: 7_675_912, rank: 2 },
      { id: 'exon-3', start: 7_684_894, end: 7_685_135, rank: 3 },
      { id: 'exon-4', start: 7_689_017, end: 7_690_000, rank: 4 },
    ],
  },
  {
    id: 'tx-tp53-202',
    name: 'TP53-202',
    chromosome: 'chr17',
    start: 7_665_901,
    end: 7_690_000,
    strand: STRAND_PLUS,
    geneId: 'gene-tp53',
    transcriptId: 'ENST00000455265',
    transcriptType: 'protein_coding',
    exons: [
      { id: 'exon-1', start: 7_665_901, end: 7_666_099, rank: 1 },
      { id: 'exon-2', start: 7_675_663, end: 7_675_912, rank: 2 },
      { id: 'exon-3', start: 7_684_894, end: 7_685_135, rank: 3 },
    ],
  },
  {
    id: 'tx-tp53-003',
    name: 'TP53-003',
    chromosome: 'chr17',
    start: 7_666_025,
    end: 7_689_152,
    strand: STRAND_PLUS,
    geneId: 'gene-tp53',
    transcriptId: 'ENST00000420265',
    transcriptType: 'processed_transcript',
    exons: [
      { id: 'exon-1', start: 7_666_025, end: 7_666_099, rank: 1 },
      { id: 'exon-2', start: 7_684_894, end: 7_685_135, rank: 2 },
    ],
  },
]

/** A TP53-like gene (fixture coordinates) used by demos and tests. */
export const TP53_FIXTURE: Gene = {
  id: 'gene-tp53',
  symbol: 'TP53',
  chromosome: 'chr17',
  start: 7_665_901,
  end: 7_690_000,
  strand: STRAND_PLUS,
  geneId: 'ENSG00000141510',
  biotype: 'protein_coding',
  transcripts: tp53Transcripts,
}

/** A reverse-strand fixture gene to exercise strand-aware rendering. */
export const BRCA1_LIKE_FIXTURE: Gene = {
  id: 'gene-brca1',
  symbol: 'BRCA1',
  chromosome: 'chr17',
  start: 43_044_295,
  end: 43_125_483,
  strand: '-' as const,
  geneId: 'ENSG00000012048',
  biotype: 'protein_coding',
  transcripts: [
    {
      id: 'tx-brca1-001',
      name: 'BRCA1-001',
      chromosome: 'chr17',
      start: 43_044_295,
      end: 43_125_483,
      strand: '-' as const,
      geneId: 'gene-brca1',
      transcriptId: 'ENST00000357654',
      transcriptType: 'protein_coding',
      exons: [
        { id: 'exon-1', start: 43_044_295, end: 43_044_468, rank: 1 },
        { id: 'exon-2', start: 43_064_129, end: 43_064_571, rank: 2 },
        { id: 'exon-3', start: 43_125_260, end: 43_125_483, rank: 3 },
      ],
    },
  ],
}
