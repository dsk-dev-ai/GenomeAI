import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GenomeTrackDefinition } from './useGenomeBrowser'
import { useGenomeBrowser } from './useGenomeBrowser'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function RenderBrowser({
  tracks,
  debounceMs,
}: {
  tracks: GenomeTrackDefinition[]
  debounceMs?: number
}) {
  const browser = useGenomeBrowser({
    initialViewport: { chromosome: 'chr1', start: 1, end: 100 },
    tracks,
    debounceMs,
  })
  return (
    <div>
      <span data-testid="viewport">
        {browser.viewport.chromosome}:{browser.viewport.start}-{browser.viewport.end}
      </span>
      {browser.trackResults.map((track) => (
        <span key={track.id} data-testid={`status-${track.id}`}>
          {track.status}:{track.errorMessage ?? ''}
        </span>
      ))}
      <button type="button" data-testid="zoom-in" onClick={browser.zoomIn}>
        zoom in
      </button>
      <button type="button" data-testid="reset" onClick={browser.reset}>
        reset
      </button>
    </div>
  )
}

describe('useGenomeBrowser', () => {
  it('mounts each track as its own request', async () => {
    const loadGenes = vi.fn().mockResolvedValue([])
    const loadVariants = vi.fn().mockResolvedValue([])
    const tracks: GenomeTrackDefinition[] = [
      { id: 'genes', label: 'Genes', kind: 'genes', loader: loadGenes },
      { id: 'variants', label: 'Variants', kind: 'variants', loader: loadVariants },
    ]

    render(<RenderBrowser tracks={tracks} />)

    await waitFor(() => expect(loadGenes).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(loadVariants).toHaveBeenCalledTimes(1))
    expect(screen.getByTestId('status-genes').textContent).toBe('empty:')
    expect(screen.getByTestId('status-variants').textContent).toBe('empty:')
  })

  it('requests the initial viewport interval', async () => {
    const loadGenes = vi.fn().mockResolvedValue([])
    const tracks: GenomeTrackDefinition[] = [
      { id: 'genes', label: 'Genes', kind: 'genes', loader: loadGenes },
    ]

    render(<RenderBrowser tracks={tracks} />)
    await waitFor(() => expect(loadGenes).toHaveBeenCalledTimes(1))
    expect(loadGenes.mock.calls[0][0]).toEqual({
      chromosome: 'chr1',
      start: 1,
      end: 100,
    })
  })

  it('surfaces a track error through the per-track status', async () => {
    const loadGenes = vi.fn().mockRejectedValue(new Error('genes unavailable'))
    const loadVariants = vi.fn().mockResolvedValue([])
    const tracks: GenomeTrackDefinition[] = [
      { id: 'genes', label: 'Genes', kind: 'genes', loader: loadGenes },
      { id: 'variants', label: 'Variants', kind: 'variants', loader: loadVariants },
    ]

    render(<RenderBrowser tracks={tracks} />)

    await waitFor(() =>
      expect(screen.getByTestId('status-genes').textContent).toBe('error:genes unavailable'),
    )
    expect(screen.getByTestId('status-variants').textContent).toBe('empty:')
  })

  it('refetches when the debounced viewport settles on a new region', async () => {
    vi.useFakeTimers()
    const loadGenes = vi.fn().mockResolvedValue([])
    const tracks: GenomeTrackDefinition[] = [
      { id: 'genes', label: 'Genes', kind: 'genes', loader: loadGenes },
    ]

    render(<RenderBrowser tracks={tracks} debounceMs={200} />)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0)
    })
    expect(loadGenes).toHaveBeenCalledTimes(1)

    // Zoom in → navigates viewport → debounced refetch after 200ms.
    fireEvent.click(screen.getByTestId('zoom-in'))
    await act(async () => {
      await vi.advanceTimersByTimeAsync(250)
    })

    // The debounce timer fires a setTimeout-based refetch alongside the
    // per-viewport effect; assert the interval changed to the zoomed window.
    expect(loadGenes).toHaveBeenCalledTimes(2)
    const lastInterval = loadGenes.mock.calls[1][0]
    expect(lastInterval.end - lastInterval.start + 1).toBeLessThan(100)

    vi.useRealTimers()
  })
})
