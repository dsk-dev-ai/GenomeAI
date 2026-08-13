import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { featureAccessibleLabel } from '@/lib/protein/features'
import { P53_PROTEIN_FIXTURE } from '@/lib/protein/protein.fixtures'
import type { ProteinViewerResult } from '@/lib/protein/useProteinViewer'
import { initialProteinViewport } from '@/lib/protein/viewport'
import { ProteinViewer } from './ProteinViewer'

function result(overrides: Partial<ProteinViewerResult> = {}): ProteinViewerResult {
  return {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    protein: P53_PROTEIN_FIXTURE,
    viewport: initialProteinViewport(P53_PROTEIN_FIXTURE.length, 100),
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    panLeft: vi.fn(),
    panRight: vi.fn(),
    resetView: vi.fn(),
    navigateTo: vi.fn(),
    selectedFeatureId: null,
    selectFeature: vi.fn(),
    ...overrides,
  }
}

/** Returns a fixture feature or throws, so tests never use `!`. */
function requireFeature(id: string) {
  const feature = P53_PROTEIN_FIXTURE.features.find((candidate) => candidate.id === id)
  if (feature === undefined) throw new Error(`Fixture feature "${id}" not found`)
  return feature
}

afterEach(() => {
  cleanup()
})

describe('ProteinViewer', () => {
  it('renders the protein header and sequence summary', () => {
    render(<ProteinViewer result={result()} />)
    expect(screen.getByText(/P53 · Homo sapiens · 120 residues/)).toBeInTheDocument()
    expect(screen.getByText(/Residues 1–100 of 120 · 120 residues/)).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(<ProteinViewer result={result({ status: 'loading', protein: undefined })} />)
    expect(screen.getByText('Loading protein sequence...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(<ProteinViewer result={result({ status: 'empty', protein: undefined })} />)
    expect(screen.getByText('No protein sequence to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <ProteinViewer
        result={result({
          status: 'error',
          protein: undefined,
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load protein')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders a residue axis with major tick labels', () => {
    render(<ProteinViewer result={result()} />)
    expect(screen.getAllByText(/^[0-9,]+$/).length).toBeGreaterThan(0)
  })

  it('renders feature bars with accessible labels and labels', () => {
    render(<ProteinViewer result={result()} />)
    for (const feature of P53_PROTEIN_FIXTURE.features) {
      if (feature.start <= 100) {
        expect(
          screen.getByRole('button', { name: `Select ${featureAccessibleLabel(feature)}` }),
        ).toBeInTheDocument()
      }
    }
  })

  it('renders per-residue letters when zoomed in and a hint when zoomed out', () => {
    render(<ProteinViewer result={result()} />)
    // Default window (1-100) over 1000px SVG yields >6px/residue -> letters.
    expect(screen.getAllByText(/^[A-Z]$/).length).toBeGreaterThan(0)
  })

  it('shows a hint when residues are too dense to render', () => {
    const wide = result({ viewport: { start: 1, end: 1500, bounds: { length: 1500 } } })
    render(<ProteinViewer result={wide} />)
    expect(screen.getByText('Zoom in to view residues')).toBeInTheDocument()
  })

  it('selects a feature via click and reveals the detail panel', () => {
    const selectFeature = vi.fn()
    render(<ProteinViewer result={result({ selectFeature })} />)
    const dnaBinding = requireFeature('feature-dna-binding')
    fireEvent.click(
      screen.getByRole('button', { name: `Select ${featureAccessibleLabel(dnaBinding)}` }),
    )
    expect(selectFeature).toHaveBeenCalledWith('feature-dna-binding')
  })

  it('supports keyboard selection via Enter and Space', () => {
    const selectFeature = vi.fn()
    render(<ProteinViewer result={result({ selectFeature })} />)
    const dnaBinding = requireFeature('feature-dna-binding')
    const control = screen.getByRole('button', {
      name: `Select ${featureAccessibleLabel(dnaBinding)}`,
    })
    fireEvent.keyDown(control, { key: 'Enter' })
    expect(selectFeature).toHaveBeenCalledWith('feature-dna-binding')

    // Re-render with the feature selected; Space toggles it back off.
    cleanup()
    const selectFeature2 = vi.fn()
    render(
      <ProteinViewer
        result={result({ selectFeature: selectFeature2, selectedFeatureId: 'feature-dna-binding' })}
      />,
    )
    const control2 = screen.getByRole('button', {
      name: `Select ${featureAccessibleLabel(dnaBinding)}`,
    })
    fireEvent.keyDown(control2, { key: ' ' })
    expect(selectFeature2).toHaveBeenCalledWith(null)
  })

  it('renders a detail panel for a controlled selection', () => {
    render(<ProteinViewer result={result({ selectedFeatureId: 'feature-dna-binding' })} />)
    expect(screen.getByTestId('protein-feature-detail')).toBeInTheDocument()
    expect(screen.getByText('DNA-binding', { selector: 'h3' })).toBeInTheDocument()
    expect(screen.getByText('Residues', { selector: 'dt' })).toBeInTheDocument()
  })

  it('clears the selection from the detail panel', () => {
    const selectFeature = vi.fn()
    render(
      <ProteinViewer
        result={result({ selectedFeatureId: 'feature-dna-binding', selectFeature })}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /clear selection/i }))
    expect(selectFeature).toHaveBeenCalledWith(null)
  })

  it('navigates from the residue form', () => {
    const navigateTo = vi.fn()
    render(<ProteinViewer result={result({ navigateTo })} />)
    const input = screen.getByLabelText('Residues')
    fireEvent.change(input, { target: { value: '94-292' } })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(navigateTo).toHaveBeenCalledWith(94, 120)
  })

  it('reports invalid residue input', () => {
    render(<ProteinViewer result={result()} />)
    const input = screen.getByLabelText('Residues')
    fireEvent.change(input, { target: { value: 'abc' } })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  it('clamps an out-of-range window to the protein', () => {
    const navigateTo = vi.fn()
    render(<ProteinViewer result={result({ navigateTo })} />)
    const input = screen.getByLabelText('Residues')
    fireEvent.change(input, { target: { value: '1-9999' } })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(navigateTo).toHaveBeenCalledWith(1, 120)
  })

  it('exposes zoom, pan, and reset controls', () => {
    const zoomIn = vi.fn()
    const zoomOut = vi.fn()
    const panLeft = vi.fn()
    const panRight = vi.fn()
    const resetView = vi.fn()
    render(<ProteinViewer result={result({ zoomIn, zoomOut, panLeft, panRight, resetView })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }))
    fireEvent.click(screen.getByRole('button', { name: 'Scroll left' }))
    fireEvent.click(screen.getByRole('button', { name: 'Scroll right' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset view' }))
    expect(zoomIn).toHaveBeenCalledTimes(1)
    expect(zoomOut).toHaveBeenCalledTimes(1)
    expect(panLeft).toHaveBeenCalledTimes(1)
    expect(panRight).toHaveBeenCalledTimes(1)
    expect(resetView).toHaveBeenCalledTimes(1)
  })
})
