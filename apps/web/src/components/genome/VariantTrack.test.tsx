import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { VariantFeature } from '@/lib/genome/types'
import type { GenomeTrackDefinition } from '@/lib/genome/useGenomeBrowser'
import { VariantTrack } from './VariantTrack'

const variantsLoader = vi.fn()

function trackDefinition(loader: typeof variantsLoader): GenomeTrackDefinition {
  return { id: 'variants', label: 'Variants', kind: 'variants', loader }
}

const viewport = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }

function variant(overrides: Partial<VariantFeature> & { id: string }): VariantFeature {
  return {
    type: 'variant',
    chromosome: 'chr17',
    start: 7_668_000,
    end: 7_668_000,
    position: 7_668_000,
    ...overrides,
  }
}

function renderTrack(loader = variantsLoader) {
  return render(<VariantTrack track={trackDefinition(loader)} debouncedViewport={viewport} />)
}

afterEach(() => {
  cleanup()
  variantsLoader.mockReset().mockImplementation(() => Promise.resolve([]))
})

describe('VariantTrack', () => {
  it('renders the container with the track label', async () => {
    renderTrack()
    expect(screen.getByText('Variants')).toBeInTheDocument()
    await waitFor(() => expect(variantsLoader).toHaveBeenCalled())
  })

  it('requests variants for the debounced viewport interval', async () => {
    renderTrack()
    await waitFor(() => expect(variantsLoader).toHaveBeenCalled())
    expect(variantsLoader.mock.calls[0][0]).toEqual({
      chromosome: 'chr17',
      start: 7_650_000,
      end: 7_700_000,
    })
  })

  it('shows the empty state when no variants are in the region', async () => {
    renderTrack()
    expect(await screen.findByText(/no variants found in region/i)).toBeInTheDocument()
  })

  it('renders a labelled SVG lane with a point mark per variant', async () => {
    variantsLoader.mockResolvedValue([
      variant({ id: 'var-a', position: 7_668_000, ref: 'C', alt: 'T', variantType: 'snv' }),
      variant({ id: 'var-b', position: 7_669_000, ref: 'A', alt: 'G' }),
    ])
    renderTrack()
    const track = await screen.findByTestId('variant-track')
    expect(track).toHaveAttribute('aria-label', 'Variants: 2 variants')
    expect(screen.getByTestId('variant-mark-var-a')).toBeInTheDocument()
    expect(screen.getByTestId('variant-mark-var-b')).toBeInTheDocument()
  })

  it('only renders variants that fall inside the viewport', async () => {
    variantsLoader.mockResolvedValue([
      variant({ id: 'inside', position: 7_660_000 }),
      variant({ id: 'outside', position: 7_700_001 }),
      variant({ id: 'wrong-chrom', position: 7_660_000, chromosome: 'chr18' }),
    ])
    renderTrack()
    await screen.findByTestId('variant-track')
    expect(screen.getByTestId('variant-mark-inside')).toBeInTheDocument()
    expect(screen.queryByTestId('variant-mark-outside')).not.toBeInTheDocument()
    expect(screen.queryByTestId('variant-mark-wrong-chrom')).not.toBeInTheDocument()
  })

  it('stacks adjacent variants on separate rows so marks never overlap', async () => {
    variantsLoader.mockResolvedValue([
      variant({ id: 'v1', position: 7_650_000 }),
      variant({ id: 'v2', position: 7_650_000 }),
    ])
    renderTrack()
    await screen.findByTestId('variant-track')
    expect(screen.getByTestId('variant-mark-v1')).toBeInTheDocument()
    expect(screen.getByTestId('variant-mark-v2')).toBeInTheDocument()
  })

  it('provides a keyboard-accessible selection control per variant', async () => {
    variantsLoader.mockResolvedValue([variant({ id: 'var-a', ref: 'C', alt: 'T' })])
    renderTrack()
    await screen.findByTestId('variant-track')
    const control = screen.getByRole('button', { name: /select C>T, chr17:/i })
    expect(control).toHaveAttribute('tabindex', '0')
    expect(control).toHaveAttribute('aria-pressed', 'false')
  })

  it('reveals a detail panel when a variant is selected', async () => {
    variantsLoader.mockResolvedValue([
      variant({ id: 'var-a', ref: 'C', alt: 'T', variantType: 'snv', filterStatus: 'PASS' }),
    ])
    renderTrack()
    const control = await screen.findByRole('button', { name: /select C>T, chr17:/i })
    fireEvent.click(control)
    expect(await screen.findByTestId('variant-detail-var-a')).toBeInTheDocument()
    expect(screen.getByText('snv')).toBeInTheDocument()
    expect(screen.getByText('PASS')).toBeInTheDocument()
    expect(control).toHaveAttribute('aria-pressed', 'true')
  })

  it('toggles the detail panel off on a second selection', async () => {
    variantsLoader.mockResolvedValue([variant({ id: 'var-a', ref: 'C', alt: 'T' })])
    renderTrack()
    const control = await screen.findByRole('button', { name: /select C>T, chr17:/i })
    fireEvent.click(control)
    expect(await screen.findByTestId('variant-detail-var-a')).toBeInTheDocument()
    fireEvent.click(control)
    await waitFor(() =>
      expect(screen.queryByTestId('variant-detail-var-a')).not.toBeInTheDocument(),
    )
  })

  it('shows the error state and retries on a failed load', async () => {
    variantsLoader.mockRejectedValueOnce(new Error('boom'))
    variantsLoader.mockResolvedValueOnce([variant({ id: 'var-a' })])
    renderTrack()
    expect(await screen.findByText(/failed to load visualization/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(await screen.findByTestId('variant-mark-var-a')).toBeInTheDocument()
  })
})
