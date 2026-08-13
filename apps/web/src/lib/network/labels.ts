/**
 * Display helpers for the Network Viewer (Phase 6.6).
 *
 * Labels, accessible names, colours, and detail-panel rows for graph nodes
 * and edges. Pure and UI-free so they are easy to test. Known node/edge type
 * literals get stable default colours; anything else uses a fallback and is
 * preserved verbatim.
 */

import { nodeById } from './model'
import type { Graph, GraphEdge, GraphNode } from './types'

/** Fallback fill for node types the viewer does not special-case. */
export const DEFAULT_NODE_COLOR = '#94a3b8'

/** Stable default fill colours for well-known biological node types. */
const NODE_TYPE_COLORS: Readonly<Record<string, string>> = {
  gene: '#3b82f6',
  protein: '#8b5cf6',
  variant: '#f59e0b',
  disease: '#ef4444',
  drug: '#10b981',
  transcript: '#06b6d4',
  study: '#ec4899',
  publication: '#f97316',
  pathway: '#6366f1',
  compound: '#14b8a6',
}

/** Stable default stroke colours for well-known relationship types. */
const EDGE_TYPE_COLORS: Readonly<Record<string, string>> = {
  interacts_with: '#8b5cf6',
  associated_with: '#f59e0b',
  regulates: '#3b82f6',
  expressed_in: '#06b6d4',
  causes: '#ef4444',
  targets: '#10b981',
  encodes: '#6366f1',
  participates_in: '#14b8a6',
  related_to: '#94a3b8',
  binds: '#ec4899',
}

/** Known node type literals that get a dedicated colour. */
export const KNOWN_NODE_TYPES = [
  'gene',
  'protein',
  'variant',
  'disease',
  'drug',
  'transcript',
  'study',
  'publication',
] as const

/** Known edge type literals that get a dedicated colour. */
export const KNOWN_EDGE_TYPES = [
  'interacts_with',
  'associated_with',
  'regulates',
  'expressed_in',
  'causes',
  'targets',
  'encodes',
  'participates_in',
  'related_to',
] as const

/** Fill colour for a node type (fallback for unknown types). */
export function nodeTypeColor(type: string): string {
  return NODE_TYPE_COLORS[type] ?? DEFAULT_NODE_COLOR
}

/** Stroke colour for an edge type (fallback for unknown types). */
export function edgeTypeColor(type: string): string {
  return EDGE_TYPE_COLORS[type] ?? '#94a3b8'
}

/** Human-readable form of a snake_case type, e.g. `interacts_with` -> `interacts with`. */
export function typeLabel(type: string): string {
  return type.replaceAll('_', ' ')
}

/** Display label of a node. */
export function nodeLabel(node: GraphNode): string {
  return node.label
}

/** Accessible name of a node, e.g. `TP53, gene`. */
export function nodeAccessibleLabel(node: GraphNode): string {
  return `${node.label}, ${typeLabel(node.type)}`
}

/** Display label of an edge, preferring the relationship label. */
export function edgeLabel(edge: GraphEdge): string {
  return edge.label ?? typeLabel(edge.type)
}

/** Accessible name of an edge, e.g. `TP53 interacts with P53`. */
export function edgeAccessibleLabel(edge: GraphEdge, graph: Graph): string {
  const source = nodeById(graph, edge.source)
  const target = nodeById(graph, edge.target)
  const sourceLabel = source ? source.label : edge.source
  const targetLabel = target ? target.label : edge.target
  return `${sourceLabel} ${edgeLabel(edge)} ${targetLabel}`
}

/** Labelled detail rows shown in the selected-node panel. */
export function nodeDetailLines(node: GraphNode): Array<{ label: string; value: string }> {
  const lines: Array<{ label: string; value: string }> = []
  lines.push({ label: 'Type', value: typeLabel(node.type) })
  lines.push({ label: 'Identifier', value: node.id })
  if (node.description) lines.push({ label: 'Description', value: node.description })
  if (node.metadata) {
    for (const [key, value] of Object.entries(node.metadata)) {
      lines.push({ label: key, value: String(value) })
    }
  }
  return lines
}

/** Labelled detail rows shown in the selected-edge panel. */
export function edgeDetailLines(
  edge: GraphEdge,
  graph: Graph,
): Array<{ label: string; value: string }> {
  const source = nodeById(graph, edge.source)
  const target = nodeById(graph, edge.target)
  return [
    { label: 'Relationship', value: edgeLabel(edge) },
    { label: 'Source', value: source ? source.label : edge.source },
    { label: 'Target', value: target ? target.label : edge.target },
    { label: 'Direction', value: edge.directed ? 'Directed' : 'Undirected' },
  ]
}
