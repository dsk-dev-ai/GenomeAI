import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { filterGraph } from '@/lib/network/filter'
import { nodeAccessibleLabel, typeLabel } from '@/lib/network/labels'
import { createLayout } from '@/lib/network/layout'
import { TP53_NETWORK_FIXTURE } from '@/lib/network/network.fixtures'
import type { NetworkViewerResult } from '@/lib/network/useNetworkViewer'
import { fitViewport } from '@/lib/network/viewport'

import { NetworkViewer } from './NetworkViewer'

const NETWORK_SVG_WIDTH = 1000
const NETWORK_SVG_HEIGHT = 620

function result(overrides: Partial<NetworkViewerResult> = {}): NetworkViewerResult {
  const graph = TP53_NETWORK_FIXTURE
  const layout = createLayout(graph)
  const base: NetworkViewerResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    graph,
    filteredGraph: filterGraph(graph, null),
    layout,
    viewport: fitViewport(layout, NETWORK_SVG_WIDTH, NETWORK_SVG_HEIGHT),
    filter: null,
    setFilter: vi.fn(),
    resetFilter: vi.fn(),
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    zoomAt: vi.fn(),
    panBy: vi.fn(),
    fitToView: vi.fn(),
    resetView: vi.fn(),
    selectedNodeId: null,
    selectedEdgeId: null,
    selectNode: vi.fn(),
    selectEdge: vi.fn(),
    clearSelection: vi.fn(),
  }
  return { ...base, ...overrides }
}

function requireNode(id: string) {
  const node = TP53_NETWORK_FIXTURE.nodes.find((candidate) => candidate.id === id)
  if (node === undefined) throw new Error(`Fixture node "${id}" not found`)
  return node
}

afterEach(() => {
  cleanup()
})

describe('NetworkViewer', () => {
  it('renders the network header and summary', () => {
    render(<NetworkViewer result={result()} />)
    expect(
      screen.getByText(/Illustrative gene\/protein\/disease\/drug relationships/),
    ).toBeInTheDocument()
    expect(screen.getByText(/11 nodes/)).toBeInTheDocument()
    expect(screen.getByText(/12 edges/)).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(<NetworkViewer result={result({ status: 'loading', graph: undefined })} />)
    expect(screen.getByText('Loading network...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(<NetworkViewer result={result({ status: 'empty', graph: undefined })} />)
    expect(screen.getByText('No network data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <NetworkViewer
        result={result({
          status: 'error',
          graph: undefined,
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load network')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders every node as a keyboard-accessible selection control', () => {
    render(<NetworkViewer result={result()} />)
    for (const node of TP53_NETWORK_FIXTURE.nodes) {
      expect(
        screen.getByRole('button', { name: `Select ${nodeAccessibleLabel(node)}` }),
      ).toBeInTheDocument()
    }
  })

  it('renders edges as keyboard-accessible selection controls', () => {
    render(<NetworkViewer result={result()} />)
    expect(
      screen.getByRole('button', { name: 'Select edge: TP53 encodes P53' }),
    ).toBeInTheDocument()
  })

  it('selects a node via click', () => {
    const selectNode = vi.fn()
    render(<NetworkViewer result={result({ selectNode })} />)
    const tp53 = requireNode('n-gene-tp53')
    fireEvent.click(screen.getByRole('button', { name: `Select ${nodeAccessibleLabel(tp53)}` }))
    expect(selectNode).toHaveBeenCalledWith('n-gene-tp53')
  })

  it('supports keyboard selection via Enter and Space', () => {
    const selectNode = vi.fn()
    render(<NetworkViewer result={result({ selectNode })} />)
    const tp53 = requireNode('n-gene-tp53')
    const control = screen.getByRole('button', { name: `Select ${nodeAccessibleLabel(tp53)}` })
    fireEvent.keyDown(control, { key: 'Enter' })
    expect(selectNode).toHaveBeenCalledWith('n-gene-tp53')

    // Re-render with the node selected; Space toggles it back off.
    cleanup()
    const selectNode2 = vi.fn()
    render(
      <NetworkViewer result={result({ selectNode: selectNode2, selectedNodeId: 'n-gene-tp53' })} />,
    )
    const control2 = screen.getByRole('button', { name: `Select ${nodeAccessibleLabel(tp53)}` })
    fireEvent.keyDown(control2, { key: ' ' })
    expect(selectNode2).toHaveBeenCalledWith(null)
  })

  it('renders a detail panel for a controlled node selection', () => {
    render(<NetworkViewer result={result({ selectedNodeId: 'n-gene-tp53' })} />)
    expect(screen.getByTestId('network-selection-detail')).toBeInTheDocument()
    expect(screen.getByText('TP53', { selector: 'h3' })).toBeInTheDocument()
    expect(screen.getByText('Type', { selector: 'dt' })).toBeInTheDocument()
  })

  it('renders a detail panel for a controlled edge selection', () => {
    render(<NetworkViewer result={result({ selectedEdgeId: 'e-tp53-p53' })} />)
    expect(screen.getByTestId('network-selection-detail')).toBeInTheDocument()
    expect(screen.getByText(typeLabel('encodes'), { selector: 'h3' })).toBeInTheDocument()
    expect(screen.getByText('Direction', { selector: 'dt' })).toBeInTheDocument()
  })

  it('clears the selection from the detail panel', () => {
    const clearSelection = vi.fn()
    render(<NetworkViewer result={result({ selectedNodeId: 'n-gene-tp53', clearSelection })} />)
    fireEvent.click(screen.getByRole('button', { name: /clear selection/i }))
    expect(clearSelection).toHaveBeenCalledTimes(1)
  })

  it('exposes zoom and fit controls', () => {
    const zoomIn = vi.fn()
    const zoomOut = vi.fn()
    const resetView = vi.fn()
    render(<NetworkViewer result={result({ zoomIn, zoomOut, resetView })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }))
    fireEvent.click(screen.getByRole('button', { name: 'Fit to view' }))
    expect(zoomIn).toHaveBeenCalledTimes(1)
    expect(zoomOut).toHaveBeenCalledTimes(1)
    expect(resetView).toHaveBeenCalledTimes(1)
  })

  it('applies a node-type filter and clears filters', () => {
    const setFilter = vi.fn()
    const resetFilter = vi.fn()
    const activeFilter = { nodeTypes: new Set(['gene']) }
    render(<NetworkViewer result={result({ setFilter, resetFilter, filter: activeFilter })} />)
    const nodeSelect = screen.getByRole('combobox', { name: 'Filter by node type' })
    fireEvent.change(nodeSelect, { target: { value: 'gene' } })
    expect(setFilter).toHaveBeenCalledTimes(1)
    const filter = setFilter.mock.calls[0][0] as { nodeTypes?: Set<string> }
    expect(filter.nodeTypes?.has('gene')).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(resetFilter).toHaveBeenCalledTimes(1)
  })

  it('shows a message when the filter removes every node', () => {
    render(<NetworkViewer result={result({ filteredGraph: { id: 'g', nodes: [], edges: [] } })} />)
    expect(screen.getByText('No nodes match the current filter.')).toBeInTheDocument()
  })
})
