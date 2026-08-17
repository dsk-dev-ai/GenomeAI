import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE } from './advanced.fixtures'
import { useVolcanoPlot } from './useVolcanoPlot'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useVolcanoPlot>) => void
  options?: Parameters<typeof useVolcanoPlot>[0]
}) {
  const model = useVolcanoPlot(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

function renderHook(options: Parameters<typeof useVolcanoPlot>[0] = {}) {
  let model: ReturnType<typeof useVolcanoPlot> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useVolcanoPlot> {
      if (model === undefined) {
        throw new Error('useVolcanoPlot did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useVolcanoPlot', () => {
  it('loads a dataset and reports success', async () => {
    const loader = vi.fn(async () => DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.dataset?.id).toBe('volcano-differential-expression')
  })

  it('reports empty for an empty dataset', async () => {
    const empty = { id: 'empty', title: 'Empty', points: [] }
    const loader = vi.fn(async () => empty)
    renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('volcano down'))
      .mockResolvedValueOnce(DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('volcano down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('derives domains and applies default thresholds', async () => {
    const loader = vi.fn(async () => DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.model.domains).toBeDefined()
    expect(captured.model.domains?.significance.min).toBe(0)
    expect(captured.model.thresholds).toEqual({ effectThreshold: 1, significanceThreshold: 2 })
  })

  it('accepts custom thresholds', async () => {
    const loader = vi.fn(async () => DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({
      loader,
      thresholds: { effectThreshold: 2, significanceThreshold: 3 },
    })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.model.thresholds).toEqual({ effectThreshold: 2, significanceThreshold: 3 })
  })

  it('selects and clears a point', async () => {
    const loader = vi.fn(async () => DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    act(() => captured.model.selectPoint('TP53'))
    await waitFor(() => expect(captured.model.selectedKey).toBe('TP53'))
    act(() => captured.model.clearSelection())
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })

  it('clears the selection when a new dataset loads', async () => {
    const first = {
      id: 'a',
      title: 'A',
      points: [{ identifier: 'g1', effect_size: 1, significance: 2 }],
    }
    const second = {
      id: 'b',
      title: 'B',
      points: [{ identifier: 'g1', effect_size: -1, significance: 3 }],
    }
    const loader = vi.fn().mockResolvedValueOnce(first).mockResolvedValueOnce(second)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})
    act(() => captured.model.selectPoint('g1'))
    await waitFor(() => expect(captured.model.selectedKey).toBe('g1'))

    act(() => captured.model.refetch())
    await waitFor(() => expect(captured.model.dataset?.id).toBe('b'))
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })

  it('clears the selection when passed null', async () => {
    const loader = vi.fn(async () => DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    act(() => captured.model.selectPoint('TP53'))
    await waitFor(() => expect(captured.model.selectedKey).toBe('TP53'))
    act(() => captured.model.selectPoint(null))
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })
})
