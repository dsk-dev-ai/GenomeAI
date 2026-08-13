/**
 * Deterministic graph layout (Phase 6.6).
 *
 * Implements one strong default layout — a **concentric** layout that places
 * high-degree nodes at the centre and fans lower-degree nodes out in rings,
 * matching how biological networks usually look (a few hubs, many leaves).
 *
 * The layout is fully deterministic: nodes are sorted by (degree desc, id
 * asc) and placed at evenly spaced angles with a per-ring golden-angle
 * offset. No randomness is involved, so the same input graph always produces
 * the same positions. This satisfies the "same input, stable output"
 * requirement without needing a seeded PRNG.
 *
 * Future layouts (force-directed, hierarchical, circular, tree, compound)
 * plug in behind the `LayoutStrategy` interface in `createLayout`.
 */

import { nodeDegrees } from './model'
import type { Graph, GraphLayout, GraphPoint } from './types'

/** Node radius the layout plans for (used to avoid ring overlaps). */
export const NODE_RADIUS = 16

/** Space kept between node edges on a ring (graph units). */
export const RING_NODE_GAP = 8

/** Minimum radius of the innermost ring (graph units). */
export const MIN_RING_RADIUS = 64

/** Radius added per ring of degree (graph units). */
export const RING_RADIUS_STEP = 72

/** Golden angle (radians) used to offset each ring so spokes don't align. */
const GOLDEN_ANGLE = (Math.PI * 2) / ((1 + Math.sqrt(5)) / 2)

/** A layout strategy: maps a graph to a deterministic `GraphLayout`. */
export type LayoutStrategy = (graph: Graph, options?: LayoutOptions) => GraphLayout

export interface LayoutOptions {
  /** Graph units of space kept between neighbour nodes on a ring. */
  nodeGap?: number
  /** Radius (graph units) of the innermost ring. */
  minRingRadius?: number
  /** Extra radius (graph units) added per ring. */
  ringStep?: number
  /** Reserved for future stochastic layouts; ignored by concentric. */
  seed?: number
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

/** Ring radius large enough that `count` nodes do not overlap. */
function ringRadiusFor(count: number, ringIndex: number, options: LayoutOptions): number {
  const minRadius = options.minRingRadius ?? MIN_RING_RADIUS
  const step = options.ringStep ?? RING_RADIUS_STEP
  const nodeGap = options.nodeGap ?? RING_NODE_GAP
  // A lone innermost node sits exactly at the centre.
  if (ringIndex === 0 && count === 1) return 0
  const base = minRadius + ringIndex * step
  const diameter = NODE_RADIUS * 2 + nodeGap
  const needed = (count * diameter) / (Math.PI * 2)
  return Math.max(base, needed)
}

/**
 * Arranges nodes in degree-descending concentric rings. Deterministic per
 * graph. Disconnected components simply share the outer rings, so the layout
 * is well-defined for any graph.
 */
export function concentricLayout(graph: Graph, options: LayoutOptions = {}): GraphLayout {
  if (graph.nodes.length === 0) return emptyLayout()

  const degrees = nodeDegrees(graph)
  const ordered = [...graph.nodes].sort(
    (a, b) => (degrees.get(b.id) ?? 0) - (degrees.get(a.id) ?? 0) || a.id.localeCompare(b.id),
  )

  // A distinct ring per distinct degree value (descending = inner rings).
  const degreeToRing = new Map<number, number>()
  let ringIndex = 0
  for (const node of ordered) {
    const degree = degrees.get(node.id) ?? 0
    if (!degreeToRing.has(degree)) {
      degreeToRing.set(degree, ringIndex)
      ringIndex += 1
    }
  }

  // Group ordered nodes into their ring, preserving order within a ring.
  const ringNodes = new Map<number, typeof ordered>()
  for (const node of ordered) {
    const degree = degrees.get(node.id) ?? 0
    const ring = degreeToRing.get(degree) ?? 0
    const list = ringNodes.get(ring) ?? []
    list.push(node)
    ringNodes.set(ring, list)
  }

  const positions = new Map<string, GraphPoint>()
  for (const [ring, nodes] of ringNodes) {
    const radius = ringRadiusFor(nodes.length, ring, options)
    const startAngle = ring * GOLDEN_ANGLE
    nodes.forEach((node, index) => {
      if (radius === 0) {
        positions.set(node.id, { x: 0, y: 0 })
        return
      }
      const angle = startAngle + (index * Math.PI * 2) / nodes.length
      positions.set(node.id, {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
      })
    })
  }

  return layoutFromPositions(graph, positions)
}

/** Builds a `GraphLayout` (bounds + centre) from explicit positions. */
export function layoutFromPositions(
  graph: Graph,
  positions: ReadonlyMap<string, GraphPoint>,
): GraphLayout {
  if (graph.nodes.length === 0) return emptyLayout()
  let minX = Number.POSITIVE_INFINITY
  let minY = Number.POSITIVE_INFINITY
  let maxX = Number.NEGATIVE_INFINITY
  let maxY = Number.NEGATIVE_INFINITY
  for (const node of graph.nodes) {
    const point = positions.get(node.id)
    if (point === undefined || !Number.isFinite(point.x) || !Number.isFinite(point.y)) {
      throw new Error(`Layout is missing a finite position for node "${node.id}".`)
    }
    minX = Math.min(minX, point.x)
    minY = Math.min(minY, point.y)
    maxX = Math.max(maxX, point.x)
    maxY = Math.max(maxY, point.y)
  }
  const width = maxX - minX
  const height = maxY - minY
  return {
    positions,
    minX,
    minY,
    maxX,
    maxY,
    centerX: minX + width / 2,
    centerY: minY + height / 2,
    width,
    height,
  }
}

/** Built-in layout strategies, keyed by name. */
export const LAYOUT_STRATEGIES: Readonly<Record<string, LayoutStrategy>> = {
  concentric: concentricLayout,
}

/** Names of the built-in layout strategies. */
export type LayoutName = keyof typeof LAYOUT_STRATEGIES

/**
 * Runs the named layout strategy (defaults to `concentric`). Throws for
 * unknown strategy names so callers catch configuration mistakes early.
 */
export function createLayout(
  graph: Graph,
  name: LayoutName = 'concentric',
  options: LayoutOptions = {},
): GraphLayout {
  const strategy = LAYOUT_STRATEGIES[name]
  if (strategy === undefined) {
    throw new Error(`Unknown graph layout strategy "${String(name)}".`)
  }
  return strategy(graph, options)
}
