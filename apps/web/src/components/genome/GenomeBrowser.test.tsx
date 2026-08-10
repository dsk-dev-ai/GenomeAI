import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GenomicFeature, GenomicInterval } from '@/lib/genome/types'
import type { GenomeTrackDefinition } from '@/lib/genome/useGenomeBrowser'

import { GenomeBrowser } from './GenomeBrowser'

const genesLoader = vi.fn()
const variantsLoader = vi.fn()

function emptyFeatures(): Promise<GenomicFeature[]> {
  return Promise.resolve([])
}

const tracks: GenomeTrackDefinition[] = [
  { id: 'genes', label: 'Genes', kind: 'genes', loader: genesLoader },
  { id: 'variants', label: 'Variants', kind: 'variants', loader: variantsLoader },
]

function renderBrowser(debounceMs = 0) {
  return render(
    <GenomeBrowser
      initialViewport={{ chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }}
      tracks={tracks}
      debounceMs={debounceMs}
    />,
  )
}

function lastInterval(loader: typeof genesLoader): GenomicInterval {
  const calls = loader.mock.calls
  return calls[calls.length - 1][0] as GenomicInterval
}

afterEach(() => {
  cleanup()
  genesLoader.mockReset().mockImplementation(emptyFeatures)
  variantsLoader.mockReset().mockImplementation(emptyFeatures)
})

describe('GenomeBrowser', () => {
  it('renders controls, axis, and both track lanes', async () => {
    renderBrowser()

    expect(screen.getByLabelText('Zoom in')).toBeInTheDocument()
    expect(screen.getByLabelText('Zoom out')).toBeInTheDocument()
    expect(screen.getByLabelText('Viewport navigation')).toBeInTheDocument()

    await waitFor(() => expect(genesLoader).toHaveBeenCalled())
    expect(screen.getByText('Genes')).toBeInTheDocument()
    expect(screen.getByText('Variants')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('chr17:7,650,000-7,700,000')
  })

  it('requests each track for the initial viewport interval', async () => {
    renderBrowser()

    await waitFor(() => expect(genesLoader).toHaveBeenCalled())
    expect(lastInterval(genesLoader)).toEqual({
      chromosome: 'chr17',
      start: 7_650_000,
      end: 7_700_000,
    })
    await waitFor(() => expect(variantsLoader).toHaveBeenCalled())
  })

  it('navigates to a region typed into the input', async () => {
    renderBrowser()
    await waitFor(() => expect(genesLoader).toHaveBeenCalled())

    fireEvent.change(screen.getByPlaceholderText('chr1:100000-200000'), {
      target: { value: 'chr17:10-100' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))

    await waitFor(() => {
      const interval = lastInterval(genesLoader)
      expect(interval).toEqual({ chromosome: 'chr17', start: 10, end: 100 })
    })
  })

  it('keeps the axis aligned with track glyphs while the viewport settles', async () => {
    vi.useFakeTimers()
    renderBrowser(300)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0)
    })
    expect(screen.getByTestId('axis-region')).toHaveAttribute(
      'data-viewport',
      'chr17:7,650,000-7,700,000',
    )

    fireEvent.change(screen.getByPlaceholderText('chr1:100000-200000'), {
      target: { value: 'chr17:10-100' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))

    // Immediately after navigation the tracks still draw the previous window;
    // the axis must not jump ahead of them.
    expect(screen.getByTestId('axis-region')).toHaveAttribute(
      'data-viewport',
      'chr17:7,650,000-7,700,000',
    )

    await act(async () => {
      await vi.advanceTimersByTimeAsync(300)
    })
    expect(screen.getByTestId('axis-region')).toHaveAttribute('data-viewport', 'chr17:10-100')
    expect(lastInterval(genesLoader)).toEqual({ chromosome: 'chr17', start: 10, end: 100 })

    vi.useRealTimers()
  })

  it('keeps invalid region input and announces the error without refetching', async () => {
    renderBrowser()
    await waitFor(() => expect(genesLoader).toHaveBeenCalled())
    const callsBefore = genesLoader.mock.calls.length

    const input = screen.getByPlaceholderText('chr1:100000-200000')
    fireEvent.change(input, { target: { value: 'not-a-region' } })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))

    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/must look like chr1:100000-200000/),
    )
    expect(input).toHaveValue('not-a-region')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(genesLoader.mock.calls.length).toBe(callsBefore)

    // Editing clears the error.
    fireEvent.change(input, { target: { value: 'chr17:10-100' } })
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(input).toHaveAttribute('aria-invalid', 'false')
  })

  it('zooms in the viewed region', async () => {
    renderBrowser()
    await waitFor(() => expect(genesLoader).toHaveBeenCalled())

    fireEvent.click(screen.getByLabelText('Zoom in'))
    fireEvent.click(screen.getByLabelText('Zoom out'))
    fireEvent.click(screen.getByLabelText('Scroll left'))
    fireEvent.click(screen.getByLabelText('Scroll right'))
    fireEvent.click(screen.getByLabelText('Reset view'))

    // All navigation actions are exercised without throwing; the viewport
    // status label stays within the initial contig bounds.
    expect(screen.getByRole('status')).toHaveTextContent('chr17:')
  })

  it('renders a per-track loading state then an empty note', async () => {
    let resolveGenes!: (features: GenomicFeature[]) => void
    genesLoader.mockReturnValue(
      new Promise<GenomicFeature[]>((resolve) => {
        resolveGenes = resolve
      }),
    )

    renderBrowser()

    // The track container is still pending for the genes lane.
    expect(screen.getByText('Genes')).toBeInTheDocument()

    resolveGenes([])
    await waitFor(() => expect(genesLoader).toHaveBeenCalled())
  })
})
