'use client'

import { useCallback, useMemo, useRef } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import {
  ARROW_SIZE,
  EDGE_HIT_STROKE_WIDTH,
  EDGE_STROKE_WIDTH,
  NETWORK_SVG_HEIGHT,
  NETWORK_SVG_WIDTH,
  edgeScreenPoints,
  nodeScreenBox,
} from '@/lib/network/geometry'
import {
  edgeAccessibleLabel,
  edgeDetailLines,
  edgeTypeColor,
  nodeAccessibleLabel,
  nodeDetailLines,
  nodeLabel,
  nodeTypeColor,
  typeLabel,
} from '@/lib/network/labels'
import { NODE_RADIUS } from '@/lib/network/layout'
import { availableEdgeTypes, availableNodeTypes, edgeById, nodeById } from '@/lib/network/model'
import type { GraphEdge, GraphNode } from '@/lib/network/types'
import type { NetworkViewerResult } from '@/lib/network/useNetworkViewer'

function NetworkSummary({ result }: { result: NetworkViewerResult }) {
  const graph = result.graph
  if (graph === undefined) return null
  const filtered = result.filteredGraph
  const filteredOut = graph.nodes.length - filtered.nodes.length > 0
  return (
    <output className="text-xs text-gray-500" aria-live="polite">
      {filtered.nodes.length.toLocaleString('en-US')} nodes ·{' '}
      {filtered.edges.length.toLocaleString('en-US')} edges
      {filteredOut ? ' (filtered)' : ''} · {graph.nodes.length.toLocaleString('en-US')} total nodes
    </output>
  )
}

function NetworkControls({ result }: { result: NetworkViewerResult }) {
  const graph = result.graph
  const nodeTypes = useMemo(() => (graph ? availableNodeTypes(graph) : []), [graph])
  const edgeTypes = useMemo(() => (graph ? availableEdgeTypes(graph) : []), [graph])

  const nodeFilter = result.filter?.nodeTypes
  const edgeFilter = result.filter?.edgeTypes

  const setNodeFilter = (value: string) => {
    const next = {
      ...(result.filter ?? {}),
      nodeTypes: value === 'all' ? undefined : new Set([value]),
    }
    result.setFilter(next.nodeTypes === undefined && next.edgeTypes === undefined ? null : next)
  }

  const setEdgeFilter = (value: string) => {
    const next = {
      ...(result.filter ?? {}),
      edgeTypes: value === 'all' ? undefined : new Set([value]),
    }
    result.setFilter(next.nodeTypes === undefined && next.edgeTypes === undefined ? null : next)
  }

  return (
    <div className="flex w-full flex-wrap items-center gap-2">
      <fieldset
        className="flex items-center gap-1 border-0 p-0"
        aria-label="Graph viewport navigation"
      >
        <legend className="sr-only">Graph viewport navigation</legend>
        {[
          { label: 'Zoom in', action: result.zoomIn, glyph: '+' },
          { label: 'Zoom out', action: result.zoomOut, glyph: '\u2212' },
          { label: 'Fit to view', action: result.resetView, glyph: '\u26F6' },
        ].map((control) => (
          <button
            key={control.label}
            type="button"
            onClick={control.action}
            aria-label={control.label}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
          >
            {control.glyph}
          </button>
        ))}
      </fieldset>
      {nodeTypes.length > 0 ? (
        <label className="flex items-center gap-1 text-sm text-gray-600">
          <span className="sr-only">Filter by node type</span>
          <select
            value={nodeFilter === undefined ? 'all' : [...nodeFilter][0]}
            onChange={(event) => setNodeFilter(event.target.value)}
            aria-label="Filter by node type"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="all">All node types</option>
            {nodeTypes.map((type) => (
              <option key={type} value={type}>
                {typeLabel(type)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {edgeTypes.length > 0 ? (
        <label className="flex items-center gap-1 text-sm text-gray-600">
          <span className="sr-only">Filter by relationship</span>
          <select
            value={edgeFilter === undefined ? 'all' : [...edgeFilter][0]}
            onChange={(event) => setEdgeFilter(event.target.value)}
            aria-label="Filter by relationship"
            className="rounded-md border border-gray-300 px-2 py-1 text-sm"
          >
            <option value="all">All relationships</option>
            {edgeTypes.map((type) => (
              <option key={type} value={type}>
                {typeLabel(type)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {result.filter !== null ? (
        <button
          type="button"
          onClick={result.resetFilter}
          aria-label="Clear filters"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
        >
          Clear filters
        </button>
      ) : null}
    </div>
  )
}

function EdgeElement({ edge, result }: { edge: GraphEdge; result: NetworkViewerResult }) {
  const graph = result.graph
  if (graph === undefined) return null
  const points = edgeScreenPoints(edge, result.layout, result.viewport)
  const selected = edge.id === result.selectedEdgeId
  const label = edgeAccessibleLabel(edge, graph)
  const color = edgeTypeColor(edge.type)
  return (
    <g data-testid={`edge-${edge.id}`}>
      <title>{label}</title>
      <line
        x1={points.x1}
        y1={points.y1}
        x2={points.x2}
        y2={points.y2}
        stroke={color}
        strokeWidth={selected ? EDGE_STROKE_WIDTH + 2 : EDGE_STROKE_WIDTH}
        markerEnd={edge.directed ? 'url(#network-edge-arrow)' : undefined}
      />
      {selected ? (
        <text x={points.mx} y={points.my - 8} textAnchor="middle" fontSize={11} fill="#475569">
          {typeLabel(edge.type)}
        </text>
      ) : null}
      <line
        role="button"
        aria-label={`Select edge: ${label}`}
        aria-pressed={selected}
        tabIndex={0}
        x1={points.x1}
        y1={points.y1}
        x2={points.x2}
        y2={points.y2}
        stroke="transparent"
        strokeWidth={EDGE_HIT_STROKE_WIDTH}
        fill="none"
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            result.selectEdge(selected ? null : edge.id)
          }
        }}
        onClick={() => result.selectEdge(selected ? null : edge.id)}
      />
    </g>
  )
}

function NodeElement({ node, result }: { node: GraphNode; result: NetworkViewerResult }) {
  const position = result.layout.positions.get(node.id)
  if (position === undefined) return null
  const selected = node.id === result.selectedNodeId
  const label = nodeAccessibleLabel(node)
  const box = nodeScreenBox(position, result.viewport)
  const scale = result.viewport.scale
  const centerX = box.x + box.width / 2
  const centerY = box.y + NODE_RADIUS * scale
  return (
    <g data-testid={`node-${node.id}`}>
      <title>{nodeLabel(node)}</title>
      <circle
        cx={centerX}
        cy={centerY}
        r={NODE_RADIUS * scale}
        fill={nodeTypeColor(node.type)}
        stroke={selected ? '#0f172a' : 'none'}
        strokeWidth={selected ? 3 : 0}
      />
      <text
        x={centerX}
        y={centerY + NODE_RADIUS * scale + 12 * scale}
        textAnchor="middle"
        fontSize={12 * scale}
        fill="#334155"
      >
        {node.label}
      </text>
      <rect
        role="button"
        aria-label={`Select ${label}`}
        aria-pressed={selected}
        tabIndex={0}
        x={box.x}
        y={box.y}
        width={box.width}
        height={box.height}
        fill="transparent"
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            result.selectNode(selected ? null : node.id)
          }
        }}
        onClick={() => result.selectNode(selected ? null : node.id)}
      />
    </g>
  )
}

function NetworkGraph({ result }: { result: NetworkViewerResult }) {
  const graph = result.graph
  if (graph === undefined) return null

  const nodes = result.filteredGraph.nodes
  const edges = result.filteredGraph.edges
  const hasNodes = nodes.length > 0

  const onWheel = useCallback(
    (event: React.WheelEvent<SVGSVGElement>) => {
      event.preventDefault()
      const rect = event.currentTarget.getBoundingClientRect()
      const cx = event.clientX - rect.left
      const cy = event.clientY - rect.top
      const factor = event.deltaY < 0 ? 1.2 : 1 / 1.2
      result.zoomAt(factor, cx, cy)
    },
    [result],
  )

  const pointerDrag = useRef<{ x: number; y: number } | null>(null)

  return (
    <svg
      width={NETWORK_SVG_WIDTH}
      height={NETWORK_SVG_HEIGHT}
      viewBox={`0 0 ${NETWORK_SVG_WIDTH} ${NETWORK_SVG_HEIGHT}`}
      // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps the
      // interactive node/edge controls inside the accessibility tree (see GenomeBrowser).
      role="group"
      aria-label={`${graph.metadata?.title ?? graph.id} network: ${nodes.length} nodes, ${edges.length} edges shown`}
      data-testid="network-svg"
      className="w-full rounded-md border border-gray-200 bg-white"
      onWheel={onWheel}
      onPointerDown={(event) => {
        pointerDrag.current = { x: event.clientX, y: event.clientY }
      }}
      onPointerMove={(event) => {
        if (pointerDrag.current === null) return
        const dx = event.clientX - pointerDrag.current.x
        const dy = event.clientY - pointerDrag.current.y
        pointerDrag.current = { x: event.clientX, y: event.clientY }
        result.panBy(dx, dy)
      }}
      onPointerUp={() => {
        pointerDrag.current = null
      }}
      onPointerLeave={() => {
        pointerDrag.current = null
      }}
    >
      <title>{graph.metadata?.title ?? graph.id}</title>
      <defs>
        <marker
          id="network-edge-arrow"
          viewBox="0 0 10 10"
          refX="9"
          refY="5"
          markerWidth={ARROW_SIZE}
          markerHeight={ARROW_SIZE}
          orient="auto-start-reverse"
        >
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
        </marker>
      </defs>
      {hasNodes ? (
        <g>
          {edges.map((edge) => (
            <EdgeElement key={edge.id} edge={edge} result={result} />
          ))}
          {nodes.map((node) => (
            <NodeElement key={node.id} node={node} result={result} />
          ))}
        </g>
      ) : (
        <g>
          <text
            x={NETWORK_SVG_WIDTH / 2}
            y={NETWORK_SVG_HEIGHT / 2}
            textAnchor="middle"
            fontSize={14}
            fill="#94a3b8"
          >
            No nodes match the current filter.
          </text>
        </g>
      )}
    </svg>
  )
}

function NetworkDetail({ result }: { result: NetworkViewerResult }) {
  const graph = result.graph
  if (graph === undefined) return null
  const node = result.selectedNodeId !== null ? nodeById(graph, result.selectedNodeId) : undefined
  const edge = result.selectedEdgeId !== null ? edgeById(graph, result.selectedEdgeId) : undefined
  if (node === undefined && edge === undefined) return null

  const title =
    node !== undefined ? nodeLabel(node) : edge !== undefined ? typeLabel(edge.type) : ''
  const lines =
    node !== undefined
      ? nodeDetailLines(node)
      : edge !== undefined
        ? edgeDetailLines(edge, graph)
        : []
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby="network-selection-heading"
      data-testid="network-selection-detail"
    >
      <h3 id="network-selection-heading" className="text-sm font-semibold text-gray-900">
        {title}
      </h3>
      <dl className="grid w-full grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
        {lines.map((line) => (
          <div key={line.label} className="flex gap-2 text-sm">
            <dt className="text-gray-500">{line.label}</dt>
            <dd className="text-gray-900">{line.value}</dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        onClick={result.clearSelection}
        className="mt-2 w-fit rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
      >
        Clear selection
      </button>
    </section>
  )
}

export interface NetworkViewerProps {
  /** View model produced by `useNetworkViewer`. */
  result: NetworkViewerResult
  /** Container heading. */
  title?: string
}

/**
 * Biological Network Viewer (Phase 6.6).
 *
 * Renders a typed relationship graph as an interactive 2D SVG: deterministic
 * layout, pan/zoom/fit, node + edge selection, node/edge type filtering, and
 * a readable detail panel. Consumes a `NetworkViewerResult` from
 * `useNetworkViewer`; all data transformation stays in `lib/network`.
 */
export function NetworkViewer({ result, title = 'Biological Network Viewer' }: NetworkViewerProps) {
  return (
    <VisualizationContainer
      title={title}
      description={
        result.graph?.metadata?.description ??
        (result.graph
          ? `${result.graph.nodes.length} nodes · ${result.graph.edges.length} edges`
          : undefined)
      }
      status={result.status}
      error={result.error}
      loadingLabel="Loading network..."
      emptyMessage="No network data to show."
      errorTitle="Failed to load network"
      onRetry={result.refetch}
    >
      {result.status === 'success' && result.graph ? (
        <div className="flex w-full flex-col gap-2">
          <NetworkSummary result={result} />
          <NetworkControls result={result} />
          <NetworkGraph result={result} />
          <NetworkDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}
