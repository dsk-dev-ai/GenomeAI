/**
 * Graph model helpers (Phase 6.6).
 *
 * Pure lookups and derived sets over a `Graph`. Normalization (dedupe,
 * dangling-edge removal, deterministic ordering) lives in `normalize.ts`;
 * filtering in `filter.ts`; neither belongs in a React component.
 */

import type { Graph, GraphEdge, GraphNode, GraphNodeType } from './types'

/** Node with the given id, or `undefined`. */
export function nodeById(graph: Graph, id: string): GraphNode | undefined {
  return graph.nodes.find((node) => node.id === id)
}

/** Edge with the given id, or `undefined`. */
export function edgeById(graph: Graph, edgeId: string): GraphEdge | undefined {
  return graph.edges.find((edge) => edge.id === edgeId)
}

/** True when the graph contains a node with this id. */
export function hasNode(graph: Graph, id: string): boolean {
  return nodeById(graph, id) !== undefined
}

/** Number of incident edges of a node (undirected count). */
export function nodeDegree(graph: Graph, nodeId: string): number {
  let degree = 0
  for (const edge of graph.edges) {
    if (edge.source === nodeId || edge.target === nodeId) degree += 1
  }
  return degree
}

/** Degree (incident edge count) for every node, keyed by node id. */
export function nodeDegrees(graph: Graph): ReadonlyMap<string, number> {
  const degrees = new Map<string, number>()
  for (const node of graph.nodes) {
    degrees.set(node.id, 0)
  }
  for (const edge of graph.edges) {
    degrees.set(edge.source, (degrees.get(edge.source) ?? 0) + 1)
    degrees.set(edge.target, (degrees.get(edge.target) ?? 0) + 1)
  }
  return degrees
}

/** Edges incident to a node (as source or target). */
export function edgesForNode(graph: Graph, nodeId: string): GraphEdge[] {
  return graph.edges.filter((edge) => edge.source === nodeId || edge.target === nodeId)
}

/** Sorted unique node types present in the graph. */
export function availableNodeTypes(graph: Graph): GraphNodeType[] {
  return [...new Set(graph.nodes.map((node) => node.type))].sort()
}

/** Sorted unique edge types present in the graph. */
export function availableEdgeTypes(graph: Graph): string[] {
  return [...new Set(graph.edges.map((edge) => edge.type))].sort()
}

/** True when a graph id, nodes, and edges are all well-formed. */
export function isValidGraph(graph: Graph): boolean {
  if (graph.id.length === 0) return false
  const ids = new Set(graph.nodes.map((node) => node.id))
  if (ids.size !== graph.nodes.length) return false
  for (const node of graph.nodes) {
    if (node.id.length === 0 || node.label.length === 0) return false
  }
  for (const edge of graph.edges) {
    if (edge.id.length === 0) return false
    if (edge.source === edge.target) return false
    if (!ids.has(edge.source) || !ids.has(edge.target)) return false
  }
  return true
}
