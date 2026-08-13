/**
 * Graph filtering (Phase 6.6).
 *
 * `filterGraph` applies a `GraphFilter` (node types and/or edge types),
 * drops edges whose endpoints were filtered out (no dangling edges), and
 * preserves the graph id and node/edge order. Deterministic and independent
 * of the UI, so it is fully unit-testable.
 */

import type { Graph, GraphFilter } from './types'

function nodeMatches(nodeType: string, filter: GraphFilter | null): boolean {
  if (filter === null || filter.nodeTypes === undefined) return true
  return filter.nodeTypes.has(nodeType)
}

function edgeMatches(edgeType: string, filter: GraphFilter | null): boolean {
  if (filter === null || filter.edgeTypes === undefined) return true
  return filter.edgeTypes.has(edgeType)
}

/**
 * Filters a graph by node type and/or edge type. `undefined` on a filter
 * dimension means "keep all". Edges are kept only when BOTH endpoints survive
 * the node filter and the edge type matches. Returns a new `Graph` (never
 * mutates the input).
 */
export function filterGraph(graph: Graph, filter: GraphFilter | null): Graph {
  if (filter === null) return graph

  const kept = new Set<string>()
  for (const node of graph.nodes) {
    if (nodeMatches(node.type, filter)) kept.add(node.id)
  }

  const nodes = graph.nodes.filter((node) => kept.has(node.id))
  const edges = graph.edges.filter(
    (edge) => kept.has(edge.source) && kept.has(edge.target) && edgeMatches(edge.type, filter),
  )

  return { ...graph, nodes, edges }
}

/** True when at least one filter dimension restricts the graph. */
export function isActiveFilter(filter: GraphFilter | null): boolean {
  if (filter === null) return false
  if (filter.nodeTypes !== undefined && filter.nodeTypes.size > 0) return true
  if (filter.edgeTypes !== undefined && filter.edgeTypes.size > 0) return true
  return false
}
