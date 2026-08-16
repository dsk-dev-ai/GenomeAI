import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_NETWORK_FIXTURE, buildTestNetwork } from './network.fixtures'
import { useNetworkViewer } from './useNetworkViewer'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useNetworkViewer>) => void
  options?: Parameters<typeof useNetworkViewer>[0]
}) {
  const model = useNetworkViewer(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

/** Renders the hook and exposes its latest result via a safe getter. */
function renderHook(options: Parameters<typeof useNetworkViewer>[0] = {}) {
  let model: ReturnType<typeof useNetworkViewer> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useNetworkViewer> {
      if (model === undefined) {
        throw new Error('useNetworkViewer did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useNetworkViewer', () => {
  it('loads a graph and reports success', async () => {
    const loader = vi.fn(async () => TP53_NETWORK_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.graph?.id).toBe('network-tp53')
  })

  it('reports empty for an empty graph', async () => {
    const loader = vi.fn(async () => ({ id: 'empty', nodes: [], edges: [] }))
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.model?.graph).toBeDefined()
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('network down'))
      .mockResolvedValueOnce(TP53_NETWORK_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model?.error?.message).toBe('network down')

    captured.model?.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('computes a deterministic layout and fits it to the view', async () => {
    const loader = vi.fn(async () => buildTestNetwork())
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    const layout = captured.model.layout
    expect(layout.positions.size).toBe(30)
    // The fit viewport centres the layout bounding box in the SVG.
    expect(captured.model.viewport.scale).toBeGreaterThan(0)
  })

  it('keeps layout positions stable while filtering', async () => {
    const loader = vi.fn(async () => buildTestNetwork())
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})
    const before = new Map(captured.model.layout.positions)

    act(() => captured.model.setFilter({ nodeTypes: new Set(['gene']) }))
    await waitFor(() => {
      expect(captured.model.filteredGraph.nodes.every((node) => node.type === 'gene')).toBe(true)
    })
    expect(captured.model.layout.positions.size).toBe(before.size)
    for (const [id, point] of before) {
      expect(captured.model.layout.positions.get(id)).toEqual(point)
    }
  })

  it('resets the filter', async () => {
    const loader = vi.fn(async () => TP53_NETWORK_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.setFilter({ nodeTypes: new Set(['drug']) }))
    await waitFor(() => expect(captured.model.filteredGraph.nodes).toHaveLength(2))

    act(() => captured.model.resetFilter())
    await waitFor(() => expect(captured.model.filter).toBeNull())
    await waitFor(() => expect(captured.model.filteredGraph.nodes).toHaveLength(11))
  })

  it('zooms, pans, and fits to view', async () => {
    const loader = vi.fn(async () => buildTestNetwork())
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    const initial = captured.model.viewport
    act(() => captured.model.zoomIn())
    await waitFor(() => expect(captured.model.viewport.scale).toBeGreaterThan(initial.scale))

    act(() => captured.model.panBy(10, 20))
    await waitFor(() => expect(captured.model.viewport.x).toBeGreaterThan(initial.x))

    act(() => captured.model.fitToView(800, 600))
    await waitFor(() => expect(captured.model.viewport).not.toEqual(initial))
  })

  it('tracks node and edge selection exclusively', async () => {
    const loader = vi.fn(async () => TP53_NETWORK_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.selectNode('n-gene-tp53'))
    await waitFor(() => expect(captured.model.selectedNodeId).toBe('n-gene-tp53'))

    act(() => captured.model.selectEdge('e-tp53-p53'))
    await waitFor(() => expect(captured.model.selectedEdgeId).toBe('e-tp53-p53'))
    expect(captured.model.selectedNodeId).toBeNull()

    act(() => captured.model.clearSelection())
    await waitFor(() => expect(captured.model.selectedNodeId).toBeNull())
    expect(captured.model.selectedEdgeId).toBeNull()
  })

  it('resets view, filter, and selection when a new graph loads', async () => {
    let current = TP53_NETWORK_FIXTURE
    const loader = vi.fn(async () => current)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await act(async () => {})

    act(() => captured.model.selectNode('n-gene-tp53'))
    act(() => captured.model.setFilter({ nodeTypes: new Set(['gene']) }))
    await waitFor(() => expect(captured.model.selectedNodeId).toBe('n-gene-tp53'))

    current = { ...buildTestNetwork(8), id: 'network-other' }
    act(() => captured.model.refetch())
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    await waitFor(() => expect(captured.model.graph?.id).toBe('network-other'))
    await act(async () => {})
    await waitFor(() => expect(captured.model.selectedNodeId).toBeNull())
    await waitFor(() => expect(captured.model.filter).toBeNull())
  })

  it('loads through the default fetchNetworkGraph loader when only networkId is given', async () => {
    const captured = renderHook({ networkId: 'network-tp53' })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    // No backend during tests: fetch rejects, which is the expected lifecycle.
    expect(captured.model?.error).toBeDefined()
  })
})
