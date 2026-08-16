import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_WINDOW_COVERAGE_FIXTURE } from './advanced.fixtures'
import { useCoverageChart } from './useCoverageChart'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useCoverageChart>) => void
  options?: Parameters<typeof useCoverageChart>[0]
}) {
  const model = useCoverageChart(options)
  onModel(model)
  return (
    <output data-testid="status">
      {model.status} {model.chromosome}
    </output>
  )
}

function renderHook(options: Parameters<typeof useCoverageChart>[0] = {}) {
  let model: ReturnType<typeof useCoverageChart> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useCoverageChart> {
      if (model === undefined) {
        throw new Error('useCoverageChart did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useCoverageChart', () => {
  it('loads a dataset, selects the first chromosome, and reports success', async () => {
    const loader = vi.fn(async () => TP53_WINDOW_COVERAGE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.dataset?.id).toBe('coverage-tp53-window')
    expect(captured.model.chromosomes).toEqual(['chr17'])
    await waitFor(() => expect(captured.model.chromosome).toBe('chr17'))
    await waitFor(() => expect(captured.model.viewport).toBeDefined())
    expect(captured.model.viewport?.start).toBeGreaterThanOrEqual(1)
  })

  it('reports empty for an empty dataset', async () => {
    const empty = { id: 'empty', title: 'Empty', bins: [] }
    const loader = vi.fn(async () => empty)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('empty'))
    expect(captured.model.chromosomes).toEqual([])
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('coverage down'))
      .mockResolvedValueOnce(TP53_WINDOW_COVERAGE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('error'))
    expect(captured.model.error?.message).toBe('coverage down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('selects a chromosome explicitly', async () => {
    const multiChromosome = {
      ...TP53_WINDOW_COVERAGE_FIXTURE,
      bins: [
        ...TP53_WINDOW_COVERAGE_FIXTURE.bins,
        ...TP53_WINDOW_COVERAGE_FIXTURE.bins.map((bin) => ({ ...bin, chromosome: 'chrX' })),
      ],
    }
    const loader = vi.fn(async () => multiChromosome)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('success'))
    expect(captured.model.chromosomes).toEqual(['chr17', 'chrX'])
    act(() => captured.model.selectChromosome('chrX'))
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('chrX'))
    expect(captured.model.chromosome).toBe('chrX')
  })

  it('zooms and pans the viewport', async () => {
    const loader = vi.fn(async () => TP53_WINDOW_COVERAGE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('success'))
    await waitFor(() => expect(captured.model.viewport).toBeDefined())
    const original = captured.model.viewport as { start: number; end: number }
    const originalSpan = original.end - original.start + 1

    act(() => captured.model.zoom(0.5))
    await waitFor(() => {
      const zoomed = captured.model.viewport as { start: number; end: number }
      expect(zoomed.end - zoomed.start + 1).toBeLessThan(originalSpan)
    })
    const zoomed = captured.model.viewport as { start: number; end: number }

    act(() => captured.model.pan(10))
    await waitFor(() => {
      const panned = captured.model.viewport as { start: number; end: number }
      expect(panned.start).toBeGreaterThan(zoomed.start)
    })
  })

  it('resets the viewport to the data extent', async () => {
    const loader = vi.fn(async () => TP53_WINDOW_COVERAGE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toContain('success'))
    await waitFor(() => expect(captured.model.viewport).toBeDefined())
    act(() => captured.model.zoom(0.5))
    act(() => captured.model.resetViewport())
    await waitFor(() => {
      const viewport = captured.model.viewport as { start: number; end: number }
      // Fixture spans 7668402..7670641.
      expect(viewport.start).toBeLessThanOrEqual(7668402)
      expect(viewport.end).toBeGreaterThanOrEqual(7670641)
    })
  })
})
