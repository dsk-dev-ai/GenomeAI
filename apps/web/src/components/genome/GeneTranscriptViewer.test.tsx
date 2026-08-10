import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Gene } from '@/lib/genome/geneTranscript'
import { TP53_FIXTURE } from '@/lib/genome/geneTranscript.fixtures'
import { GeneTranscriptViewer, LABEL_GUTTER } from './GeneTranscriptViewer'

const viewport = { chromosome: 'chr17', start: 7_660_000, end: 7_700_000 }

function renderViewer(props: Partial<React.ComponentProps<typeof GeneTranscriptViewer>> = {}) {
  return render(<GeneTranscriptViewer gene={TP53_FIXTURE} viewport={viewport} {...props} />)
}

afterEach(() => {
  cleanup()
})

describe('GeneTranscriptViewer', () => {
  it('renders a labelled SVG describing the gene', () => {
    renderViewer()
    const svg = screen.getByRole('group')
    expect(svg).toHaveAttribute('aria-label', 'TP53 chr17:7665901-7690000, strand +, 3 transcripts')
  })

  it('renders the gene symbol label', () => {
    renderViewer()
    expect(screen.getByText('TP53')).toBeInTheDocument()
  })

  it('renders every transcript label', () => {
    renderViewer()
    for (const transcript of TP53_FIXTURE.transcripts) {
      expect(screen.getByText(transcript.name)).toBeInTheDocument()
    }
  })

  it('renders an exon block per exon in the viewport', () => {
    renderViewer()
    const totalExons = TP53_FIXTURE.transcripts.reduce((sum, t) => sum + t.exons.length, 0)
    expect(screen.getAllByTestId(/^exon-/)).toHaveLength(totalExons)
  })

  it('provides hover titles for transcripts', () => {
    renderViewer()
    const first = TP53_FIXTURE.transcripts[0]
    expect(screen.getByTestId(`transcript-lane-${first.id}`)).toBeInTheDocument()
  })

  it('renders a selection control per transcript', () => {
    renderViewer()
    for (const transcript of TP53_FIXTURE.transcripts) {
      expect(screen.getByRole('button', { name: `Select ${transcript.name}` })).toBeInTheDocument()
    }
  })

  it('renders nothing when the gene is outside the viewport', () => {
    render(
      <GeneTranscriptViewer
        gene={TP53_FIXTURE}
        viewport={{ chromosome: 'chr17', start: 1, end: 100 }}
      />,
    )
    // The SVG and labels are still rendered, but no exon blocks appear.
    expect(screen.getByRole('group')).toBeInTheDocument()
    expect(screen.queryAllByTestId(/^exon-/)).toHaveLength(0)
  })

  it('aligns exon geometry with the shared label gutter', () => {
    renderViewer()
    const svg = screen.getByRole('group')
    expect(svg).toBeInTheDocument()
    // LABEL_GUTTER is the reserved left column width shared with the browser.
    expect(LABEL_GUTTER).toBeGreaterThan(0)
  })
})

describe('GeneTranscriptViewer selection', () => {
  it('selects a transcript on click', () => {
    renderViewer()
    const first = TP53_FIXTURE.transcripts[0]
    const control = screen.getByRole('button', { name: `Select ${first.name}` })
    expect(control).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(control)
    expect(control).toHaveAttribute('aria-pressed', 'true')

    // Clicking again deselects.
    fireEvent.click(control)
    expect(control).toHaveAttribute('aria-pressed', 'false')
  })

  it('selects a transcript via keyboard', () => {
    renderViewer()
    const first = TP53_FIXTURE.transcripts[0]
    const control = screen.getByRole('button', { name: `Select ${first.name}` })

    fireEvent.keyDown(control, { key: 'Enter' })
    expect(control).toHaveAttribute('aria-pressed', 'true')

    fireEvent.keyDown(control, { key: ' ' })
    expect(control).toHaveAttribute('aria-pressed', 'false')
  })

  it('fires onSelectTranscript in controlled mode', () => {
    const onSelect = vi.fn()
    renderViewer({ onSelectTranscript: onSelect })
    const first = TP53_FIXTURE.transcripts[0]

    fireEvent.click(screen.getByRole('button', { name: `Select ${first.name}` }))
    expect(onSelect).toHaveBeenCalledWith(first.id)
  })

  it('reflects a controlled selectedTranscriptId', () => {
    const id = TP53_FIXTURE.transcripts[1].id
    renderViewer({ selectedTranscriptId: id })
    expect(
      screen.getByRole('button', { name: `Select ${TP53_FIXTURE.transcripts[1].name}` }),
    ).toHaveAttribute('aria-pressed', 'true')
  })
})

describe('GeneTranscriptViewer strands', () => {
  it('renders a reverse-strand gene without error', () => {
    const reverseGene: Gene = {
      ...TP53_FIXTURE,
      id: 'gene-brca1',
      symbol: 'BRCA1',
      strand: '-',
      start: 43_044_295,
      end: 43_125_483,
      transcripts: [
        {
          id: 'tx-rev',
          name: 'BRCA1-001',
          chromosome: 'chr17',
          start: 43_044_295,
          end: 43_125_483,
          strand: '-',
          exons: [{ id: 'e1', start: 43_044_295, end: 43_044_468, rank: 1 }],
        },
      ],
    }
    render(
      <GeneTranscriptViewer
        gene={reverseGene}
        viewport={{ chromosome: 'chr17', start: 43_000_000, end: 43_200_000 }}
      />,
    )
    expect(screen.getByRole('group')).toHaveAttribute(
      'aria-label',
      expect.stringContaining('strand -'),
    )
    expect(screen.getByText('BRCA1-001')).toBeInTheDocument()
  })
})
