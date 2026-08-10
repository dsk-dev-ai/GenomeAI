import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GenomeTrackDefinition } from './useGenomeBrowser'
import { useGenomeBrowser, useGenomeTrack } from './useGenomeBrowser'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function RenderViewport() {
  const browser = useGenomeBrowser({
    initialViewport: { chromosome: 'chr1', start: 1, end: 100 },
  })
  return (
    <div>
      <span data-testid="viewport">
        {browser.viewport.chromosome}:{browser.viewport.start}-{browser.viewport.end}
      </span>
      <button type="button" data-testid="zoom-in" onClick={browser.zoomIn}>
        zoom in
      </button>
      <button type="button" data-testid="zoom-out" onClick={browser.zoomOut}>
        zoom out
      </button>
      <button type="button" data-testid="pan-left" onClick={browser.panLeft}>
        pan left
      </button>
      <button type="button" data-testid="reset" onClick={browser.reset}>
        reset
      </button>
      <button
        type="button"
        data-testid="navigate-other"
        onClick={() => browser.navigateTo({ chromosome: 'chr2', start: 5, end: 50 })}
      >
        go chr2
      </button>
    </div>
  )
}

describe('useGenomeBrowser', () => {
  it('starts at the initial viewport', () => {
    render(<RenderViewport />)
    expect(screen.getByTestId('viewport').textContent).toBe('chr1:1-100')
  })

  it('zooms in and out around the viewport', () => {
    render(<RenderViewport />)
    const span = () => {
      const text = screen.getByTestId('viewport').textContent ?? ''
      const [, coords] = text.split(':')
      const [start, end] = coords.split('-').map(Number)
      return end - start + 1
    }
    fireEvent.click(screen.getByTestId('zoom-in'))
    expect(span()).toBeLessThan(100)
    fireEvent.click(screen.getByTestId('zoom-out'))
    expect(span()).toBeGreaterThan(1)
  })

  it('clears stale bounds when navigating to another chromosome', async () => {
    function Bounded() {
      const browser = useGenomeBrowser({
        initialViewport: {
          chromosome: 'chr1',
          start: 1,
          end: 100,
          bounds: { length: 500 },
        },
      })
      return (
        <div>
          <span data-testid="viewport">
            {browser.viewport.chromosome}:{browser.viewport.start}-{browser.viewport.end}
          </span>
          <span data-testid="bounds">{browser.viewport.bounds?.length ?? 'none'}</span>
          <button
            type="button"
            data-testid="navigate-other"
            onClick={() => browser.navigateTo({ chromosome: 'chr2', start: 5, end: 50 })}
          >
            go chr2
          </button>
        </div>
      )
    }
    render(<Bounded />)
    fireEvent.click(screen.getByTestId('navigate-other'))
    await waitFor(() => expect(screen.getByTestId('viewport').textContent).toBe('chr2:5-50'))
    expect(screen.getByTestId('bounds').textContent).toBe('none')
  })

  it('clamps a same-chromosome interval to known bounds', async () => {
    function Bounded() {
      const browser = useGenomeBrowser({
        initialViewport: {
          chromosome: 'chr1',
          start: 1,
          end: 100,
          bounds: { length: 500 },
        },
      })
      return (
        <div>
          <span data-testid="viewport">
            {browser.viewport.chromosome}:{browser.viewport.start}-{browser.viewport.end}
          </span>
          <button
            type="button"
            data-testid="navigate"
            onClick={() => browser.navigateTo({ chromosome: 'chr1', start: 400, end: 900 })}
          >
            go
          </button>
        </div>
      )
    }
    render(<Bounded />)
    fireEvent.click(screen.getByTestId('navigate'))
    await waitFor(() => expect(screen.getByTestId('viewport').textContent).toBe('chr1:400-500'))
  })

  it('pan left and reset keep the viewport bounded', () => {
    render(<RenderViewport />)
    fireEvent.click(screen.getByTestId('pan-left'))
    expect(screen.getByTestId('viewport').textContent).toBe('chr1:1-100')
    fireEvent.click(screen.getByTestId('reset'))
    expect(screen.getByTestId('viewport').textContent).toBe('chr1:1-100')
  })
})

function RenderTrack({ definition }: { definition: GenomeTrackDefinition }) {
  const track = useGenomeTrack(definition, {
    chromosome: 'chr1',
    start: 1,
    end: 100,
    bounds: { length: 1000 },
  })
  return (
    <div>
      <span data-testid="track-status">{track.status}</span>
      <span data-testid="track-error">{track.errorMessage ?? ''}</span>
      <span data-testid="track-data">{JSON.stringify(track.data ?? null)}</span>
    </div>
  )
}

describe('useGenomeTrack', () => {
  it('loads a track to success and exposes the features', async () => {
    const loadGenes = vi
      .fn()
      .mockResolvedValue([{ id: 'a', type: 'gene', chromosome: 'chr1', start: 10, end: 20 }])
    const definition: GenomeTrackDefinition = {
      id: 'genes',
      label: 'Genes',
      kind: 'genes',
      loader: loadGenes,
    }

    render(<RenderTrack definition={definition} />)

    await waitFor(() => expect(screen.getByTestId('track-status').textContent).toBe('success'))
    expect(loadGenes.mock.calls[0][0]).toEqual({ chromosome: 'chr1', start: 1, end: 100 })
    expect(screen.getByTestId('track-data').textContent).toContain('"type":"gene"')
  })

  it('surfaces a track error', async () => {
    const loadGenes = vi.fn().mockRejectedValue(new Error('genes unavailable'))
    const definition: GenomeTrackDefinition = {
      id: 'genes',
      label: 'Genes',
      kind: 'genes',
      loader: loadGenes,
    }

    render(<RenderTrack definition={definition} />)

    await waitFor(() => expect(screen.getByTestId('track-status').textContent).toBe('error'))
    expect(screen.getByTestId('track-error').textContent).toBe('genes unavailable')
  })

  it('refetches when the debounced viewport settles on a new region', async () => {
    vi.useFakeTimers()
    const loadGenes = vi.fn().mockResolvedValue([])
    const definition: GenomeTrackDefinition = {
      id: 'genes',
      label: 'Genes',
      kind: 'genes',
      loader: loadGenes,
    }

    function BrowserWithTrack() {
      const browser = useGenomeBrowser({
        initialViewport: { chromosome: 'chr1', start: 1, end: 100 },
        debounceMs: 200,
      })
      const track = useGenomeTrack(definition, browser.debouncedViewport)
      return (
        <div>
          <span data-testid="track-status">{track.status}</span>
          <button type="button" data-testid="zoom-in" onClick={browser.zoomIn}>
            zoom in
          </button>
        </div>
      )
    }

    render(<BrowserWithTrack />)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0)
    })
    expect(loadGenes).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByTestId('zoom-in'))
    await act(async () => {
      await vi.advanceTimersByTimeAsync(300)
    })

    expect(loadGenes).toHaveBeenCalledTimes(2)
    const lastInterval = loadGenes.mock.calls[1][0]
    expect(lastInterval.end - lastInterval.start + 1).toBeLessThan(100)

    vi.useRealTimers()
  })
})
