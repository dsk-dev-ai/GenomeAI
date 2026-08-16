import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { LONG_PROTEIN_FIXTURE, P53_PROTEIN_FIXTURE } from '@/lib/protein/protein.fixtures'
import { useProteinViewer } from './useProteinViewer'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useProteinViewer>) => void
  options?: Parameters<typeof useProteinViewer>[0]
}) {
  const model = useProteinViewer(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

/** Renders the hook and exposes its latest result via a safe getter. */
function renderHook(options: Parameters<typeof useProteinViewer>[0] = {}) {
  let model: ReturnType<typeof useProteinViewer> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useProteinViewer> {
      if (model === undefined) {
        throw new Error('useProteinViewer did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useProteinViewer', () => {
  it('loads a protein and reports success', async () => {
    const loader = vi.fn(async () => P53_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model?.protein?.name).toBe('P53')
  })

  it('opens on the first window of the protein', async () => {
    const loader = vi.fn(async () => LONG_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 1, end: 100, bounds: { length: 1500 } }),
    )
  })

  it('uses the custom default window size', async () => {
    const loader = vi.fn(async () => LONG_PROTEIN_FIXTURE)
    const captured = renderHook({ loader, defaultWindow: 25 })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 1, end: 25, bounds: { length: 1500 } }),
    )
  })

  it('reports empty for a zero-length protein', async () => {
    const loader = vi.fn(async () => ({ ...P53_PROTEIN_FIXTURE, sequence: '', length: 0 }))
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.model?.protein).toBeDefined()
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce(P53_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model?.error?.message).toBe('network down')

    captured.model?.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('zooms in and out around the window centre', async () => {
    const loader = vi.fn(async () => LONG_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})
    const before = captured.model.viewport

    act(() => captured.model.zoomIn())
    await waitFor(() => {
      const viewport = captured.model.viewport
      expect(viewport.end - viewport.start + 1).toBeLessThan(before.end - before.start + 1)
      expect(viewport.start).toBeGreaterThanOrEqual(1)
    })

    const zoomed = captured.model.viewport
    act(() => captured.model.zoomOut())
    await waitFor(() => {
      const viewport = captured.model.viewport
      expect(viewport.end - viewport.start + 1).toBeGreaterThan(zoomed.end - zoomed.start + 1)
      expect(viewport.end).toBeLessThanOrEqual(1500)
    })
  })

  it('clamps zoom-out to the full protein', async () => {
    const loader = vi.fn(async () => P53_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    for (let i = 0; i < 20; i += 1) act(() => captured.model.zoomOut())
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 1, end: 120, bounds: { length: 120 } }),
    )
  })

  it('pans by a fraction of the window and never leaves the protein', async () => {
    const loader = vi.fn(async () => LONG_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.panRight())
    await waitFor(() => expect(captured.model.viewport.start).toBeGreaterThan(1))

    for (let i = 0; i < 100; i += 1) act(() => captured.model.panRight())
    await waitFor(() => expect(captured.model.viewport.end).toBe(1500))

    act(() => captured.model.panLeft())
    await waitFor(() => expect(captured.model.viewport.end).toBeLessThan(1500))
  })

  it('navigates to an explicit window and resets to the opening window', async () => {
    const loader = vi.fn(async () => LONG_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.navigateTo(300, 400))
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 300, end: 400, bounds: { length: 1500 } }),
    )

    act(() => captured.model.resetView())
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 1, end: 100, bounds: { length: 1500 } }),
    )
  })

  it('clamps navigation to the protein length', async () => {
    const loader = vi.fn(async () => P53_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.navigateTo(1, 9999))
    await waitFor(() =>
      expect(captured.model.viewport).toEqual({ start: 1, end: 120, bounds: { length: 120 } }),
    )
  })

  it('tracks and clears the selected feature', async () => {
    const loader = vi.fn(async () => P53_PROTEIN_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    expect(captured.model?.selectedFeatureId).toBeNull()
    act(() => captured.model.selectFeature('feature-dna-binding'))
    await waitFor(() => expect(captured.model.selectedFeatureId).toBe('feature-dna-binding'))
    act(() => captured.model.selectFeature(null))
    await waitFor(() => expect(captured.model.selectedFeatureId).toBeNull())
  })

  it('loads through the default fetchProtein loader when only proteinId is given', async () => {
    const captured = renderHook({ proteinId: 'P04637' })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    // No backend during tests: fetch rejects, which is the expected lifecycle.
    expect(captured.model?.error).toBeDefined()
  })
})
