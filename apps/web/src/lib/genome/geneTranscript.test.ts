import { describe, expect, it } from 'vitest'

import {
  groupTranscriptsByGene,
  isValidExon,
  isValidGene,
  isValidTranscript,
  sortTranscripts,
  toExon,
  toGene,
  toTranscript,
} from './geneTranscript'
import type { Gene, GeneTranscript } from './geneTranscript'

function transcript(overrides: Partial<GeneTranscript> & { id: string }): GeneTranscript {
  return {
    name: overrides.id,
    chromosome: 'chr17',
    start: 100,
    end: 200,
    strand: '+',
    exons: [],
    ...overrides,
  }
}

describe('toGene', () => {
  it('normalizes a raw gene record', () => {
    const gene = toGene({
      id: 'gene-1',
      gene_id: 'ENSG00000141510',
      gene_name: 'TP53',
      biotype: 'protein_coding',
      chromosome: 'chr17',
      start_position: 7_665_901,
      end_position: 7_690_000,
      strand: '-',
    })
    expect(gene).toMatchObject({
      id: 'gene-1',
      symbol: 'TP53',
      chromosome: 'chr17',
      start: 7_665_901,
      end: 7_690_000,
      strand: '-',
      geneId: 'ENSG00000141510',
      biotype: 'protein_coding',
      transcripts: [],
    })
  })

  it('falls back to gene_id for id and symbol when name is missing', () => {
    const gene = toGene({ gene_id: 'ENSG00000141510', chromosome: 'chr17' })
    expect(gene.id).toBe('ENSG00000141510')
    expect(gene.symbol).toBe('ENSG00000141510')
  })

  it('treats an unknown strand as plus', () => {
    const gene = toGene({ chromosome: 'chr17', start_position: 1, end_position: 2 })
    expect(gene.strand).toBe('+')
  })
})

describe('toTranscript', () => {
  it('normalizes a raw transcript record with exons when present', () => {
    const tx = toTranscript({
      id: 'tx-1',
      transcript_id: 'ENST00000269305',
      transcript_name: 'TP53-201',
      transcript_type: 'protein_coding',
      chromosome: 'chr17',
      strand: '+',
      start_position: 7_665_901,
      end_position: 7_690_000,
      gene_id: 'gene-tp53',
      exons: [
        { id: 'e1', start: 7_665_901, end: 7_666_099, rank: 1 },
        { id: 'e2', start: 7_684_894, end: 7_685_135, rank: 2 },
      ],
    })
    expect(tx).toMatchObject({
      id: 'tx-1',
      name: 'TP53-201',
      transcriptId: 'ENST00000269305',
      transcriptType: 'protein_coding',
      chromosome: 'chr17',
      start: 7_665_901,
      end: 7_690_000,
      strand: '+',
      geneId: 'gene-tp53',
    })
    expect(tx.exons).toHaveLength(2)
    expect(tx.exons[0]).toMatchObject({ id: 'e1', start: 7_665_901, end: 7_666_099, rank: 1 })
  })

  it('returns empty exons when the source has none', () => {
    const tx = toTranscript({ chromosome: 'chr17', start_position: 1, end_position: 2 })
    expect(tx.exons).toEqual([])
  })

  it('drops invalid exon records', () => {
    const tx = toTranscript({
      chromosome: 'chr17',
      start_position: 1,
      end_position: 2,
      exons: [{ start: 10, end: 20 }, { start: 30, end: 20 }, 'not-an-exon'],
    })
    expect(tx.exons).toHaveLength(1)
    expect(tx.exons[0]).toMatchObject({ start: 10, end: 20 })
  })
})

describe('toExon', () => {
  it('fills missing coordinates with zeros for later filtering', () => {
    const exon = toExon({ id: 'x', rank: 1 })
    expect(exon).toMatchObject({ id: 'x', rank: 1, start: 0, end: 0 })
  })
})

describe('validators', () => {
  it('accepts well-formed exons/transcripts/genes', () => {
    expect(isValidExon({ start: 10, end: 20 })).toBe(true)
    expect(isValidTranscript(transcript({ id: 'a' }))).toBe(true)
    expect(
      isValidGene({
        id: 'g',
        symbol: 'X',
        chromosome: 'chr1',
        start: 1,
        end: 2,
        strand: '+',
        transcripts: [],
      }),
    ).toBe(true)
  })

  it('rejects reversed or non-positive spans', () => {
    expect(isValidExon({ start: 20, end: 10 })).toBe(false)
    expect(isValidExon({ start: 0, end: 0 })).toBe(false)
    expect(isValidTranscript(transcript({ id: 'a', start: 200, end: 100 }))).toBe(false)
    expect(
      isValidGene({
        id: 'g',
        symbol: 'X',
        chromosome: '',
        start: 1,
        end: 2,
        strand: '+',
        transcripts: [],
      }),
    ).toBe(false)
  })
})

describe('sortTranscripts', () => {
  it('sorts by start then end then name', () => {
    const input = [
      transcript({ id: 'c', start: 200, end: 300 }),
      transcript({ id: 'a', start: 100, end: 150 }),
      transcript({ id: 'b', start: 100, end: 200 }),
    ]
    expect(sortTranscripts(input).map((t) => t.id)).toEqual(['a', 'b', 'c'])
  })
})

describe('groupTranscriptsByGene', () => {
  const gene: Gene = {
    id: 'g1',
    symbol: 'GENE',
    chromosome: 'chr17',
    start: 100,
    end: 1000,
    strand: '+',
    transcripts: [],
  }

  it('assigns transcripts by explicit geneId link', () => {
    const tx = transcript({ id: 't1', geneId: 'g1', start: 200, end: 300 })
    const result = groupTranscriptsByGene([gene], [tx])
    expect(result).toHaveLength(1)
    expect(result[0].transcripts.map((t) => t.id)).toEqual(['t1'])
  })

  it('assigns contained transcripts by coordinate fallback', () => {
    const tx = transcript({ id: 't1', start: 200, end: 300 })
    const result = groupTranscriptsByGene([gene], [tx])
    expect(result[0].transcripts.map((t) => t.id)).toEqual(['t1'])
  })

  it('drops transcripts outside the gene span on another chromosome', () => {
    const tx = transcript({ id: 't1', chromosome: 'chr2', start: 200, end: 300 })
    const result = groupTranscriptsByGene([gene], [tx])
    expect(result[0].transcripts).toEqual([])
  })

  it('skips genes without a usable span', () => {
    const broken: Gene = { ...gene, start: 1000, end: 100 }
    expect(groupTranscriptsByGene([broken], [])).toEqual([])
  })

  it('keeps transcript order stable after grouping', () => {
    const t1 = transcript({ id: 't1', start: 500, end: 600 })
    const t2 = transcript({ id: 't2', start: 200, end: 300 })
    const result = groupTranscriptsByGene([gene], [t2, t1])
    expect(result[0].transcripts.map((t) => t.id)).toEqual(['t2', 't1'])
  })
})
