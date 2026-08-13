/**
 * TypeScript types for the Biological Network Viewer (Phase 6.6).
 *
 * ## Coordinate conventions
 *
 * Graph layout coordinates are **abstract 2D units** in a deterministic
 * layout space centred on the origin. The viewer projects them to screen
 * pixels with a 2D viewport (`NetworkViewport`: translation + scale),
 * mirroring how the genome/protein viewers map one-based intervals through
 * a linear scale. Layout is computed once per graph; pan/zoom only move the
 * viewport.
 *
 * ## Domain independence
 *
 * `GraphNode` / `GraphEdge` are deliberately generic: node and edge `type`s
 * are opaque strings (e.g. `'gene'`, `'protein'`, `'disease'`,
 * `'interacts_with'`) that the renderer maps to presentation defaults but
 * never interprets semantically. The viewer is a visualization layer, not a
 * source of scientific relationship data.
 */

/** Free-form metadata carried by a graph node or edge. */
export type GraphMetadata = Record<string, string | number | boolean>

/**
 * Type of a graph node. Known biological literals (gene, protein, variant,
 * disease, drug, transcript, study, publication, ...) get default colours;
 * any other string is preserved verbatim and rendered with the fallback
 * colour, so the viewer is not hard-wired to one annotation source.
 */
export type GraphNodeType = string

/**
 * Type of a graph edge / relationship. Known biological literals
 * (interacts_with, associated_with, regulates, expressed_in, causes,
 * targets, encodes, participates_in, related_to, ...) are preserved
 * verbatim; the viewer never asserts scientific validity.
 */
export type GraphEdgeType = string

/** A single node in a biological relationship graph. */
export interface GraphNode {
  /** Stable identifier (e.g. a gene record uuid). */
  id: string
  /** Short display label (e.g. `TP53`). */
  label: string
  /** Node class, e.g. `gene`, `protein`, `disease`, `drug`. */
  type: GraphNodeType
  /** Optional human-readable description. */
  description?: string
  /** Optional domain-specific metadata. */
  metadata?: GraphMetadata
}

/** A single relationship between two graph nodes. */
export interface GraphEdge {
  /** Stable identifier (e.g. a relationship record uuid). */
  id: string
  /** Id of the source node. */
  source: string
  /** Id of the target node. */
  target: string
  /** Relationship class, e.g. `interacts_with`, `regulates`. */
  type: GraphEdgeType
  /** Optional short display label overriding the relationship type. */
  label?: string
  /** When true the edge is drawn with an arrowhead at the target. */
  directed?: boolean
  /** Optional domain-specific metadata. */
  metadata?: GraphMetadata
}

/** A typed relationship graph consumed by the Network Viewer. */
export interface Graph {
  /** Stable identifier of the network (e.g. a network record uuid). */
  id: string
  /** Nodes in the graph (already normalized: unique, deterministic order). */
  nodes: GraphNode[]
  /** Edges in the graph (already normalized: no dangling references). */
  edges: GraphEdge[]
  /** Optional display metadata. */
  metadata?: {
    title?: string
    description?: string
  }
}

/** A 2D point in layout coordinates. */
export interface GraphPoint {
  x: number
  y: number
}

/**
 * Result of a deterministic layout: a position per node plus the layout's
 * bounding box, so views can fit-to-view without re-deriving geometry.
 */
export interface GraphLayout {
  /** Node id -> position in graph units (deterministic per graph). */
  positions: ReadonlyMap<string, GraphPoint>
  /** Bounding box of the laid-out nodes (graph units). */
  minX: number
  minY: number
  maxX: number
  maxY: number
  /** Centre of the bounding box (graph units). */
  centerX: number
  centerY: number
  /** Width of the bounding box (may be 0 for single/empty graphs). */
  width: number
  /** Height of the bounding box (may be 0 for single/empty graphs). */
  height: number
}

/**
 * The visible 2D window of the graph: a screen-space translation plus a zoom
 * scale. A layout point `p` projects to screen `(p.x * scale + x,
 * p.y * scale + y)`.
 */
export interface NetworkViewport {
  /** Screen x offset (px). */
  x: number
  /** Screen y offset (px). */
  y: number
  /** Zoom factor applied to layout coordinates. */
  scale: number
}

/**
 * Filter over a graph. `undefined` on a dimension means "keep all"; a set
 * means "keep only these node/edge types". Applied by `filterGraph`, which
 * also removes edges whose endpoints were filtered out (no dangling edges).
 */
export interface GraphFilter {
  /** Node types to keep (undefined = all). */
  nodeTypes?: ReadonlySet<string>
  /** Edge/relationship types to keep (undefined = all). */
  edgeTypes?: ReadonlySet<string>
}

/** Full viewer state (what would persist across a session). */
export interface GraphViewerState {
  viewport: NetworkViewport
  selectedNodeId: string | null
  selectedEdgeId: string | null
  filter: GraphFilter | null
}
