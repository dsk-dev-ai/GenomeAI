/**
 * Network Viewer view-model hook (Phase 6.6).
 *
 * Composes the Phase 6.1 visualization data lifecycle
 * (`useVisualizationData`) with a deterministic layout, a 2D viewport
 * (pan/zoom/fit), filtering, and node/edge selection. The whole graph is
 * loaded once per network id; pan/zoom/filter/selection are client-side only,
 * so no per-view refetch is needed.
 *
 * Layout is computed from the **full** graph and never rebuilt when the
 * filter changes, so positions stay stable while filtering. Filtering only
 * changes which nodes/edges are rendered.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { ZOOM_FACTOR } from '@/lib/genome/viewport'
import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

import { fetchNetworkGraph } from './api'
import { filterGraph } from './filter'
import { NETWORK_SVG_HEIGHT, NETWORK_SVG_WIDTH } from './geometry'
import { createLayout } from './layout'
import type { LayoutName, LayoutOptions } from './layout'
import type { Graph, GraphFilter, GraphLayout, NetworkViewport } from './types'
import { fitViewport, identityViewport, panViewport, zoomViewport } from './viewport'

/** Result shape of `useNetworkViewer`, consumed by `NetworkViewer`. */
export interface NetworkViewerResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the network load request. */
  refetch: () => void
  /** Loaded full graph, or `undefined` until success. */
  graph: Graph | undefined
  /** Graph after the active filter (an empty graph when nothing matches). */
  filteredGraph: Graph
  /** Deterministic layout of the FULL graph (stable across filters). */
  layout: GraphLayout
  /** Current 2D viewport (translation + scale). */
  viewport: NetworkViewport
  /** Active filter (null = show everything). */
  filter: GraphFilter | null
  setFilter: (filter: GraphFilter | null) => void
  resetFilter: () => void
  zoomIn: () => void
  zoomOut: () => void
  /** Zooms by a factor around a screen point (defaults to the SVG centre). */
  zoomAt: (factor: number, cx?: number, cy?: number) => void
  /** Pans by screen pixels. */
  panBy: (dx: number, dy: number) => void
  /** Fits the whole layout into a screen size (defaults to the SVG size). */
  fitToView: (width?: number, height?: number) => void
  /** Same as calling `fitToView()` with defaults. */
  resetView: () => void
  selectedNodeId: string | null
  selectedEdgeId: string | null
  /** Selects a node (clears any edge selection). */
  selectNode: (nodeId: string | null) => void
  /** Selects an edge (clears any node selection). */
  selectEdge: (edgeId: string | null) => void
  clearSelection: () => void
}

export interface UseNetworkViewerOptions {
  /** Fetches the graph (defaults to `fetchNetworkGraph(networkId)`). */
  loader?: (signal: AbortSignal) => Promise<Graph>
  /** Backend network id used when no custom loader is provided. */
  networkId?: string
  /** Layout strategy name (defaults to the deterministic concentric layout). */
  layoutName?: LayoutName
  layoutOptions?: LayoutOptions
}

const EMPTY_GRAPH: Graph = { id: '', nodes: [], edges: [] }

export function useNetworkViewer(options: UseNetworkViewerOptions = {}): NetworkViewerResult {
  const { networkId, layoutName = 'concentric', layoutOptions } = options

  const loaderRef = useRef(options.loader)
  const networkIdRef = useRef(networkId)
  loaderRef.current = options.loader
  networkIdRef.current = networkId

  const loader = useCallback((signal: AbortSignal) => {
    const custom = loaderRef.current
    if (custom !== undefined) return custom(signal)
    if (networkIdRef.current !== undefined) return fetchNetworkGraph(networkIdRef.current, signal)
    return Promise.reject(new Error('No network loader provided to useNetworkViewer.'))
  }, [])

  const { status, data, error, refetch } = useVisualizationData<Graph>(loader, {
    isEmpty: (graph) => graph.nodes.length === 0,
  })

  const graph = data
  const layout = useMemo(
    () => (graph === undefined ? emptyLayout() : createLayout(graph, layoutName, layoutOptions)),
    [graph, layoutName, layoutOptions],
  )

  const [viewport, setViewport] = useState<NetworkViewport>(identityViewport)
  const [filter, setFilter] = useState<GraphFilter | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)

  // (Re)initialize the view when a new network loads: fit-to-view, clear any
  // filter and selection.
  const loadedNetworkIdRef = useRef<string | null>(null)
  useEffect(() => {
    if (graph !== undefined && graph.id !== loadedNetworkIdRef.current) {
      loadedNetworkIdRef.current = graph.id
      setViewport(fitViewport(layout, NETWORK_SVG_WIDTH, NETWORK_SVG_HEIGHT))
      setFilter(null)
      setSelectedNodeId(null)
      setSelectedEdgeId(null)
    }
  }, [graph, layout])

  const filteredGraph = useMemo(
    () => (graph === undefined ? EMPTY_GRAPH : filterGraph(graph, filter)),
    [graph, filter],
  )

  const zoomAt = useCallback(
    (factor: number, cx = NETWORK_SVG_WIDTH / 2, cy = NETWORK_SVG_HEIGHT / 2) => {
      setViewport((current) => zoomViewport(current, factor, cx, cy))
    },
    [],
  )

  const zoomIn = useCallback(() => zoomAt(ZOOM_FACTOR), [zoomAt])
  const zoomOut = useCallback(() => zoomAt(1 / ZOOM_FACTOR), [zoomAt])

  const panBy = useCallback((dx: number, dy: number) => {
    setViewport((current) => panViewport(current, dx, dy))
  }, [])

  const fitToView = useCallback(
    (width = NETWORK_SVG_WIDTH, height = NETWORK_SVG_HEIGHT) => {
      setViewport(fitViewport(layout, width, height))
    },
    [layout],
  )

  const resetView = useCallback(() => fitToView(), [fitToView])

  const selectNode = useCallback((nodeId: string | null) => {
    setSelectedNodeId(nodeId)
    if (nodeId !== null) setSelectedEdgeId(null)
  }, [])

  const selectEdge = useCallback((edgeId: string | null) => {
    setSelectedEdgeId(edgeId)
    if (edgeId !== null) setSelectedNodeId(null)
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedNodeId(null)
    setSelectedEdgeId(null)
  }, [])

  const resetFilter = useCallback(() => setFilter(null), [])

  return {
    status,
    error,
    refetch,
    graph,
    filteredGraph,
    layout,
    viewport,
    filter,
    setFilter,
    resetFilter,
    zoomIn,
    zoomOut,
    zoomAt,
    panBy,
    fitToView,
    resetView,
    selectedNodeId,
    selectedEdgeId,
    selectNode,
    selectEdge,
    clearSelection,
  }
}

function emptyLayout(): GraphLayout {
  return {
    positions: new Map(),
    minX: 0,
    minY: 0,
    maxX: 0,
    maxY: 0,
    centerX: 0,
    centerY: 0,
    width: 0,
    height: 0,
  }
}
