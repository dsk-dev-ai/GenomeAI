import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_PATHWAY_HEATMAP_FIXTURE } from './advanced.fixtures'
import type { HeatmapDataset } from './advancedTypes'
import { heatmapCellKey } from './heatmap'
import { useHeatmap } from './useHeatmap'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useHeatmap>) => void
  options?: Parameters<typeof useHeatmap>[0]
}) {
  const model = useHeatmap(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

function renderHook(options: Parameters<typeof useHeatmap>[0] = {}) {
  let model: ReturnType<typeof useHeatmap> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useHeatmap> {
      if (model === undefined) {
        throw new Error('useHeatmap did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useHeatmap', () => {
  it('loads a dataset and reports success', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_HEATMAP_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.dataset?.id).toBe('heatmap-tp53-pathway')
  })

  it('reports empty for an empty matrix', async () => {
    const empty: HeatmapDataset = { id: 'empty', title: 'Empty', rows: [], columns: [], values: [] }
    const loader = vi.fn(async () => empty)
    renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('heatmap down'))
      .mockResolvedValueOnce(TP53_PATHWAY_HEATMAP_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('heatmap down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('derives the value domain and color scale', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_HEATMAP_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.model.domain).toBeDefined()
    expect(typeof captured.model.colorScale(0)).toBe('string')
  })

  it('selects and clears a cell', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_HEATMAP_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    const key = heatmapCellKey({ row: 'tp53', column: 'Tumor-1' })
    act(() => captured.model.selectCell(key))
    await waitFor(() => expect(captured.model.selectedKey).toBe(key))
    act(() => captured.model.clearSelection())
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })

  it('clears the selection when a new dataset loads', async () => {
    const first: HeatmapDataset = {
      id: 'a',
      title: 'A',
      rows: ['r1'],
      columns: ['c1'],
      values: [[1]],
    }
    const second: HeatmapDataset = {
      id: 'b',
      title: 'B',
      rows: ['r1'],
      columns: ['c1'],
      values: [[2]],
    }
    const loader = vi.fn().mockResolvedValueOnce(first).mockResolvedValueOnce(second)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})
    const key = heatmapCellKey({ row: 'r1', column: 'c1' })
    act(() => captured.model.selectCell(key))
    await waitFor(() => expect(captured.model.selectedKey).toBe(key))
    act(() => captured.model.refetch())
    await waitFor(() => expect(captured.model.dataset?.id).toBe('b'))
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })
})
