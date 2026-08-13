/**
 * Graph normalization (Phase 6.6).
 *
 * Turns an arbitrary `Graph` into the canonical form the viewer renders:
 *
 * - Node ids de-duplicated (first occurrence wins)
 * - Edge ids de-duplicated (first occurrence wins)
 * - Self-loops dropped (the viewer does not render them yet)
 * - Edges referencing unknown node ids dropped (no dangling references)
 * - Nodes ordered by id, edges by (source, target, type, id) so rendering
 *   and tests are deterministic
 */

import type { Graph, GraphEdge, GraphNode } from './types'

function dedupeNodes(nodes: readonly GraphNode[]): GraphNode[] {
  const seen = new Set<string>()
  const result: GraphNode[] = []
  for (const node of nodes) {
    if (seen.has(node.id)) continue
    seen.add(node.id)
    result.push(node)
  }
  return result
}

export function sortNodes(nodes: readonly GraphNode[]): GraphNode[] {
  return [...nodes].sort((a, b) => a.id.localeCompare(b.id))
}

function dedupeEdges(edges: readonly GraphEdge[]): GraphEdge[] {
  const seen = new Set<string>()
  const result: GraphEdge[] = []
  for (const edge of edges) {
    if (seen.has(edge.id)) continue
    seen.add(edge.id)
    result.push(edge)
  }
  return result
}

export function sortEdges(edges: readonly GraphEdge[]): GraphEdge[] {
  return [...edges].sort(
    (a, b) =>
      a.source.localeCompare(b.source) ||
      a.target.localeCompare(b.target) ||
      a.type.localeCompare(b.type) ||
      a.id.localeCompare(b.id),
  )
}

/**
 * Normalizes a graph: dedupes nodes/edges, drops self-loops and dangling
 * edges, and orders everything deterministically. Never mutates its input.
 */
export function normalizeGraph(graph: Graph): Graph {
  const nodeIds = new Set<string>()
  const nodes = sortNodes(dedupeNodes(graph.nodes))
  for (const node of nodes) nodeIds.add(node.id)

  const edges = sortEdges(
    dedupeEdges(graph.edges).filter((edge) => {
      if (edge.source === edge.target) return false
      return nodeIds.has(edge.source) && nodeIds.has(edge.target)
    }),
  )

  return { ...graph, nodes, edges }
}
