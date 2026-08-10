'use client'

import { useState } from 'react'

import type { Gene, GeneTranscript } from '@/lib/genome/geneTranscript'
import {
  EXON_HEIGHT,
  GENE_LABEL_X,
  GENE_LANE_HEIGHT,
  INTRON_WIDTH,
  LABEL_Y_OFFSET,
  TRANSCRIPT_LANE_HEIGHT,
  exonToPixels,
  geneTranscriptHeight,
  intervalToPixels,
  layoutTranscriptLanes,
  transcriptToPixels,
} from '@/lib/genome/geneTranscriptGeometry'
import { createScale } from '@/lib/genome/geometry'
import type { GenomeViewport } from '@/lib/genome/types'

/** Pixel width of the left label gutter shared by all lanes. */
export const LABEL_GUTTER = 96

/** Pixel width of the SVG drawing area used as the `viewBox` base. */
export const SVG_WIDTH = 1000

/** Vertical centre of the gene lane. */
const GENE_Y = Math.round(GENE_LANE_HEIGHT / 2)

/** Colours for forward-strand rendering (mirrors the Genome Browser). */
const FORWARD_FILL = '#2563eb'
const REVERSE_FILL = '#7c3aed'
const INTRON_STROKE = '#94a3b8'
const LABEL_FILL = '#475569'
const SELECTED_FILL = '#db2777'

/** Arrowhead length for the strand indicator (px). */
const ARROW_LENGTH = 6
const ARROW_HEIGHT = 7

export interface GeneTranscriptViewerProps {
  /** The gene to draw, together with its transcripts. */
  gene: Gene
  /** Visible window; defines the genomic→pixel scale. */
  viewport: GenomeViewport
  /** Currently selected transcript id (controlled mode). */
  selectedTranscriptId?: string | null
  /** Fires when a transcript is selected/deselected (controlled mode). */
  onSelectTranscript?: (transcriptId: string | null) => void
}

/** Accessible label describing one transcript row. */
function transcriptLabel(transcript: GeneTranscript): string {
  const exons = transcript.exons.length > 0 ? `, ${transcript.exons.length} exons` : ''
  return `${transcript.name} ${transcript.chromosome}:${transcript.start}-${transcript.end}, strand ${transcript.strand}${exons}`
}

/**
 * Gene / Transcript visualization (Phase 6.3).
 *
 * Renders one gene as a lane plus one lane per transcript, with intron
 * connectors, exon blocks, strand indicators, and labels — all positioned
 * with the shared Genome Browser scale so the output stays aligned with any
 * Genome Browser axis drawn from the same viewport.
 *
 * ## Accessibility
 *
 * The SVG carries a descriptive `aria-label` of the whole gene. Each
 * transcript row is a keyboard-focusable control (`role="button"`) with an
 * accessible name; pressing Enter/Space selects it, and the selected row is
 * visually highlighted and announced via `aria-pressed`. Hover reveals a
 * native `<title>` tooltip on transcripts and exons.
 */
export function GeneTranscriptViewer({
  gene,
  viewport,
  selectedTranscriptId: controlledSelected,
  onSelectTranscript,
}: GeneTranscriptViewerProps) {
  const [internalSelected, setInternalSelected] = useState<string | null>(null)

  const selectedTranscriptId =
    controlledSelected !== undefined ? controlledSelected : internalSelected

  const handleSelect = (transcriptId: string) => {
    const next = selectedTranscriptId === transcriptId ? null : transcriptId
    if (onSelectTranscript !== undefined) {
      onSelectTranscript(next)
    } else {
      setInternalSelected(next)
    }
  }

  const lanes = layoutTranscriptLanes(gene.transcripts)
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - LABEL_GUTTER)
  const height = geneTranscriptHeight(gene.transcripts.length)
  const geneSpan = intervalToPixels(scale, viewport, gene.start, gene.end)
  const selected = gene.transcripts.some((t) => t.id === selectedTranscriptId)
    ? selectedTranscriptId
    : null

  const geneAriaLabel = `${gene.symbol} ${gene.chromosome}:${gene.start}-${gene.end}, strand ${gene.strand}, ${gene.transcripts.length} transcripts`

  return (
    <svg
      viewBox={`0 0 ${SVG_WIDTH} ${height}`}
      className="w-full"
      role="img"
      aria-label={geneAriaLabel}
    >
      {/* Gene lane */}
      <g>
        <title>
          {geneAriaLabel}
          {gene.biotype ? `, ${gene.biotype}` : ''}
        </title>
        <text x={GENE_LABEL_X} y={GENE_Y + 4} fontSize={11} fontWeight={600} fill={LABEL_FILL}>
          {gene.symbol}
        </text>
        {geneSpan.visible ? (
          <GeneGlyph
            span={geneSpan.span}
            y={GENE_Y}
            height={6}
            strand={gene.strand}
            fill={gene.strand === '-' ? REVERSE_FILL : FORWARD_FILL}
          />
        ) : null}
      </g>

      {/* Transcript lanes */}
      {gene.transcripts.map((transcript, index) => {
        const lane = lanes[index]
        const bodySpan = transcriptToPixels(scale, viewport, transcript)
        const isSelected = transcript.id === selected
        const strandFill = transcript.strand === '-' ? REVERSE_FILL : FORWARD_FILL

        return (
          <g
            key={transcript.id}
            transform={`translate(0 ${lane.y})`}
            data-testid={`transcript-lane-${transcript.id}`}
          >
            <title>{transcriptLabel(transcript)}</title>
            <text
              x={GENE_LABEL_X}
              y={LABEL_Y_OFFSET + TRANSCRIPT_LANE_HEIGHT / 2}
              fontSize={10}
              fill={LABEL_FILL}
            >
              {transcript.name}
            </text>

            {/* Intron connector */}
            {bodySpan.visible ? (
              <line
                x1={LABEL_GUTTER + bodySpan.span.x}
                x2={LABEL_GUTTER + bodySpan.span.x + bodySpan.span.width}
                y1={TRANSCRIPT_LANE_HEIGHT / 2}
                y2={TRANSCRIPT_LANE_HEIGHT / 2}
                stroke={INTRON_STROKE}
                strokeWidth={INTRON_WIDTH}
              />
            ) : null}

            {/* Exon blocks */}
            {transcript.exons.map((exon, exonIndex) => {
              const exonSpan = exonToPixels(scale, viewport, exon)
              if (!exonSpan.visible) return null
              return (
                <g
                  key={`${exon.id ?? exonIndex}`}
                  data-testid={`exon-${transcript.id}-${exon.id ?? exonIndex}`}
                >
                  <title>
                    Exon {exon.rank ?? exonIndex + 1}: {exon.start}-{exon.end}
                  </title>
                  <rect
                    x={LABEL_GUTTER + exonSpan.span.x}
                    y={TRANSCRIPT_LANE_HEIGHT / 2 - EXON_HEIGHT / 2}
                    width={Math.max(1, exonSpan.span.width)}
                    height={EXON_HEIGHT}
                    rx={1}
                    fill={isSelected ? SELECTED_FILL : strandFill}
                  />
                </g>
              )
            })}

            {/* Strand arrow over the connector */}
            {bodySpan.visible && transcript.exons.length === 0 ? (
              <StrandArrow
                x={LABEL_GUTTER + bodySpan.span.x}
                width={bodySpan.span.width}
                y={TRANSCRIPT_LANE_HEIGHT / 2}
                strand={transcript.strand}
              />
            ) : null}

            {/* Selection control */}
            <rect
              role="button"
              aria-label={`Select ${transcript.name}`}
              aria-pressed={isSelected}
              tabIndex={0}
              x={0}
              y={0}
              width={SVG_WIDTH}
              height={TRANSCRIPT_LANE_HEIGHT}
              fill="transparent"
              data-transcript-id={transcript.id}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  handleSelect(transcript.id)
                }
              }}
              onClick={() => handleSelect(transcript.id)}
            />
          </g>
        )
      })}
    </svg>
  )
}

/** A strand-aware gene span with a direction arrowhead. */
function GeneGlyph({
  span,
  y,
  height,
  strand,
  fill,
}: {
  span: { x: number; width: number }
  y: number
  height: number
  strand: '+' | '-'
  fill: string
}) {
  const x = LABEL_GUTTER + span.x
  const bodyWidth = Math.max(1, span.width - ARROW_LENGTH)
  const bodyX = strand === '+' ? x : x + ARROW_LENGTH
  const arrow =
    strand === '+'
      ? `M ${x + bodyWidth} ${y - height / 2} l ${ARROW_LENGTH} ${height / 2} l ${-ARROW_LENGTH} ${height / 2} Z`
      : `M ${x + ARROW_LENGTH} ${y - height / 2} l ${-ARROW_LENGTH} ${height / 2} l ${ARROW_LENGTH} ${height / 2} Z`
  return (
    <g>
      <rect x={bodyX} y={y - height / 2} width={bodyWidth} height={height} rx={1} fill={fill} />
      <path d={arrow} fill={fill} />
    </g>
  )
}

/** Small strand arrow for a transcript with no exon blocks. */
function StrandArrow({
  x,
  width,
  y,
  strand,
}: {
  x: number
  width: number
  y: number
  strand: '+' | '-'
}) {
  const tip = strand === '+' ? x + width : x
  const base = strand === '+' ? tip - ARROW_LENGTH : tip + ARROW_LENGTH
  const points =
    strand === '+'
      ? `${tip},${y} ${base},${y - ARROW_HEIGHT / 2} ${base},${y + ARROW_HEIGHT / 2}`
      : `${tip},${y} ${base},${y - ARROW_HEIGHT / 2} ${base},${y + ARROW_HEIGHT / 2}`
  return <polygon points={points} fill={strand === '-' ? REVERSE_FILL : FORWARD_FILL} />
}
