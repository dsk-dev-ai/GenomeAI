import { describe, expect, it } from 'vitest'

import type { GeneTranscript } from './geneTranscript'
import {
  EXON_HEIGHT,
  GENE_LANE_HEIGHT,
  INTRON_WIDTH,
  TRANSCRIPT_LANE_HEIGHT,
  exonToPixels,
  geneTranscriptHeight,
  intervalToPixels,
  layoutTranscriptLanes,
  transcriptToPixels,
} from './geneTranscriptGeometry'
import { createScale } from './geometry'

const viewport = { chromosome: 'chr17', start: 100, end: 200 }

function transcript(overrides: Partial<GeneTranscript> & { id: string }): GeneTranscript {
  return {
    name: overrides.id,
    chromosome: 'chr17',
    start: 120,
    end: 180,
    strand: '+',
    exons: [],
    ...overrides,
  }
}

describe('intervalToPixels', () => {
  it('maps an inclusive interval to pixel x and width', () => {
    const scale = createScale(100, 200, 1000)
    const { span, visible } = intervalToPixels(scale, viewport, 100, 200)
    expect(visible).toBe(true)
    expect(span.x).toBe(0)
    expect(span.width).toBeCloseTo(1000)
  })

  it('clips to the viewport', () => {
    const scale = createScale(100, 200, 1000)
    const { span } = intervalToPixels(scale, viewport, 150, 250)
    // 150..200 clipped → 51 bases of the 101-base span.
    expect(span.x).toBeCloseTo(scale.toX(150))
    expect(span.width).toBeCloseTo(scale.spanToPixels(51))
  })

  it('reports invisible when entirely outside the viewport', () => {
    const scale = createScale(100, 200, 1000)
    const { visible } = intervalToPixels(scale, viewport, 1, 50)
    expect(visible).toBe(false)
  })

  it('handles a single-base interval', () => {
    const scale = createScale(100, 200, 1000)
    const { span } = intervalToPixels(scale, viewport, 150, 150)
    expect(span.width).toBeCloseTo(1000 / 101)
  })
})

describe('exonToPixels', () => {
  it('returns the pixel span of an exon', () => {
    const scale = createScale(100, 200, 1010)
    const { span, visible } = exonToPixels(scale, viewport, { start: 110, end: 130 })
    expect(visible).toBe(true)
    expect(span.x).toBeCloseTo(scale.toX(110))
    expect(span.width).toBeCloseTo(scale.spanToPixels(21))
  })

  it('marks a fully-out-of-viewport exon invisible', () => {
    const scale = createScale(100, 200, 1010)
    const { visible } = exonToPixels(scale, viewport, { start: 300, end: 400 })
    expect(visible).toBe(false)
  })
})

describe('transcriptToPixels', () => {
  it('uses the transcript span for the intron connector', () => {
    const scale = createScale(100, 200, 1000)
    const { span, visible } = transcriptToPixels(scale, viewport, transcript({ id: 't' }))
    expect(visible).toBe(true)
    expect(span.x).toBeCloseTo(scale.toX(120))
    expect(span.width).toBeCloseTo(scale.spanToPixels(61))
  })
})

describe('layoutTranscriptLanes', () => {
  it('gives each transcript its own lane', () => {
    const lanes = layoutTranscriptLanes([transcript({ id: 'a' }), transcript({ id: 'b' })])
    expect(lanes).toHaveLength(2)
    expect(lanes[0]).toEqual({ index: 0, y: GENE_LANE_HEIGHT })
    expect(lanes[1]).toEqual({ index: 1, y: GENE_LANE_HEIGHT + TRANSCRIPT_LANE_HEIGHT })
  })

  it('handles the empty transcript list', () => {
    expect(layoutTranscriptLanes([])).toEqual([])
  })
})

describe('geneTranscriptHeight', () => {
  it('grows with transcript count', () => {
    expect(geneTranscriptHeight(0)).toBe(GENE_LANE_HEIGHT)
    expect(geneTranscriptHeight(2)).toBe(GENE_LANE_HEIGHT + 2 * TRANSCRIPT_LANE_HEIGHT)
  })
})

// Keep visual constants under test so changes are intentional.
describe('visual constants', () => {
  it('keeps exon blocks smaller than their lane', () => {
    expect(EXON_HEIGHT).toBeLessThan(TRANSCRIPT_LANE_HEIGHT)
    expect(INTRON_WIDTH).toBeGreaterThan(0)
  })
})
