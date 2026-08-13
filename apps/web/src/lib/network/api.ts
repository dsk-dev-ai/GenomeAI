/**
 * Network data adapter (Phase 6.6).
 *
 * Defines the raw record shapes a future GenomeAI network endpoint is
 * expected to return and the normalization seam (`toGraphNode`,
 * `toGraphEdge`, `graphFromRecords`) the viewer uses. It reuses the shared
 * `API_BASE_URL`, `GenomeApiError`, and guard helpers from
 * `lib/genome/api.ts`.
 *
 * ## API limitation
 *
 * The GenomeAI backend does **not** yet expose a network endpoint. This
 * module documents the expected contract and `fetchNetworkGraph` attempts
 * `GET /networks/{id}` (which will 404 today, surfacing the limitation as a
 * typed error). The demo therefore uses the isolated deterministic fixture in
 * `lib/network/network.fixtures.ts` and flips to the real adapter as soon as
 * a network endpoint exists. See `docs/visualization/network-viewer.md`.
 *
 * The browser never talks to external biological databases (STRING, Reactome,
 * BioGRID, IntAct, Open Targets, ...); those feed GenomeAI through the later
 * connector/ingestion architecture.
 */

import { API_BASE_URL, GenomeApiError, asString } from '@/lib/genome/api'

import { normalizeGraph } from './normalize'
import type { Graph, GraphEdge, GraphNode, GraphNodeType } from './types'

/** Raw record shape a future network endpoint is expected to return. */
export interface RawGraphRecord {
  id?: unknown
  nodes?: unknown
  edges?: unknown
  title?: unknown
  description?: unknown
  [key: string]: unknown
}

/** Raw node record shape. */
export interface RawGraphNodeRecord {
  id?: unknown
  label?: unknown
  node_type?: unknown
  type?: unknown
  description?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/** Raw edge record shape. */
export interface RawGraphEdgeRecord {
  id?: unknown
  source?: unknown
  target?: unknown
  relationship?: unknown
  type?: unknown
  label?: unknown
  directed?: unknown
  metadata?: unknown
  [key: string]: unknown
}

function recordIsObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asMetadata(value: unknown): Record<string, string | number | boolean> | undefined {
  if (!recordIsObject(value)) return undefined
  const entries = Object.entries(value).filter(
    (entry): entry is [string, string | number | boolean] => {
      const [, field] = entry
      return typeof field === 'string' || typeof field === 'number' || typeof field === 'boolean'
    },
  )
  return entries.length > 0 ? Object.fromEntries(entries) : undefined
}

/** Normalizes a raw node record into a `GraphNode`, or returns `undefined`. */
export function toGraphNode(record: unknown): GraphNode | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  const label = asString(record.label)
  if (id === undefined || id.length === 0) return undefined
  if (label === undefined || label.length === 0) return undefined
  const rawType = asString(record.node_type) ?? asString(record.type)
  const type: GraphNodeType = rawType === undefined || rawType.length === 0 ? 'custom' : rawType
  return {
    id,
    label,
    type,
    ...(asString(record.description) !== undefined
      ? { description: asString(record.description) }
      : {}),
    ...(asMetadata(record.metadata) !== undefined ? { metadata: asMetadata(record.metadata) } : {}),
  }
}

/** Normalizes a raw edge record into a `GraphEdge`, or returns `undefined`. */
export function toGraphEdge(record: unknown): GraphEdge | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  const source = asString(record.source)
  const target = asString(record.target)
  if (id === undefined || id.length === 0) return undefined
  if (source === undefined || target === undefined) return undefined
  const rawType = asString(record.relationship) ?? asString(record.type)
  const type = rawType === undefined || rawType.length === 0 ? 'related_to' : rawType
  return {
    id,
    source,
    target,
    type,
    ...(asString(record.label) !== undefined ? { label: asString(record.label) } : {}),
    ...(typeof record.directed === 'boolean' ? { directed: record.directed } : {}),
    ...(asMetadata(record.metadata) !== undefined ? { metadata: asMetadata(record.metadata) } : {}),
  }
}

/**
 * Builds a normalized, valid `Graph` from raw records. Invalid records are
 * dropped via `toGraphNode`/`toGraphEdge`; `normalizeGraph` then dedupes ids,
 * drops self-loops and dangling edges, and orders deterministically.
 */
export function graphFromRecords(record: unknown): Graph | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const rawNodes = Array.isArray(record.nodes) ? record.nodes : []
  const rawEdges = Array.isArray(record.edges) ? record.edges : []
  const nodes = rawNodes.map(toGraphNode).filter((node): node is GraphNode => node !== undefined)
  const edges = rawEdges.map(toGraphEdge).filter((edge): edge is GraphEdge => edge !== undefined)
  return normalizeGraph({
    id,
    nodes,
    edges,
    metadata: {
      ...(asString(record.title) !== undefined ? { title: asString(record.title) } : {}),
      ...(asString(record.description) !== undefined
        ? { description: asString(record.description) }
        : {}),
    },
  })
}

/**
 * Fetches a network by id from the (not-yet-existing) network endpoint.
 * Throws `GenomeApiError` on failure today so the limitation is explicit and
 * typed. Fixture-based demos bypass this loader.
 */
export async function fetchNetworkGraph(networkId: string, signal?: AbortSignal): Promise<Graph> {
  const response = await fetch(`${API_BASE_URL}/networks/${encodeURIComponent(networkId)}`, {
    headers: { 'Content-Type': 'application/json' },
    signal,
  })
  if (!response.ok) {
    throw new GenomeApiError(
      `GenomeAI API returned ${response.status} for network ${networkId}`,
      response.status,
    )
  }
  const payload: unknown = await response.json()
  const graph = graphFromRecords(payload)
  if (graph === undefined) {
    throw new GenomeApiError(`GenomeAI API returned an invalid payload for network ${networkId}`)
  }
  return graph
}
