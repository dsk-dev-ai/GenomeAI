/**
 * Render geometry for the Network Viewer (Phase 6.6).
 *
 * SVG constants and pure helpers used by `NetworkViewer` to turn layout
 * positions + a viewport into screen geometry. Kept separate from the
 * component so it is unit-testable without a DOM.
 */

import { NODE_RADIUS } from './layout'
import type { GraphEdge, GraphLayout, NetworkViewport } from './types'
import { projectPoint } from './viewport'

/** Default SVG drawing width (px). */
export const NETWORK_SVG_WIDTH = 1000

/** Default SVG drawing height (px). */
export const NETWORK_SVG_HEIGHT = 620

/** Screen-space arrowhead size (px) for directed edges. */
export const ARROW_SIZE = 8

/** Stroke width of edges (px). */
export const EDGE_STROKE_WIDTH = 2

/** Invisible hit-target stroke width (px) for selecting edges. */
export const EDGE_HIT_STROKE_WIDTH = 12

/** Extra label width (px) on either side of a node for hits. */
export const LABEL_PAD = 20

/** Screen-space endpoint of an edge, shortened so lines stop at node edges. */
export function edgeEndpoints(
  source: { x: number; y: number },
  target: { x: number; y: number },
): { x1: number; y1: number; x2: number; y2: number } {
  const dx = target.x - source.x
  const dy = target.y - source.y
  const distance = Math.hypot(dx, dy)
  if (distance === 0) return { x1: source.x, y1: source.y, x2: target.x, y2: target.y }
  const inset = NODE_RADIUS + 2
  const sx = source.x + (dx / distance) * inset
  const sy = source.y + (dy / distance) * inset
  const tx = target.x - (dx / distance) * inset
  const ty = target.y - (dy / distance) * inset
  return { x1: sx, y1: sy, x2: tx, y2: ty }
}

/** Screen-space midpoint of an edge (used for relationship labels). */
export function edgeMidpoint(
  source: { x: number; y: number },
  target: { x: number; y: number },
): { x: number; y: number } {
  return { x: (source.x + target.x) / 2, y: (source.y + target.y) / 2 }
}

/** Edge endpoints in screen space for a positioned edge. */
export function edgeScreenPoints(
  edge: GraphEdge,
  layout: GraphLayout,
  viewport: NetworkViewport,
): { x1: number; y1: number; x2: number; y2: number; mx: number; my: number } {
  const source = layout.positions.get(edge.source)
  const target = layout.positions.get(edge.target)
  if (source === undefined || target === undefined) {
    return { x1: 0, y1: 0, x2: 0, y2: 0, mx: 0, my: 0 }
  }
  const screenSource = projectPoint(source, viewport)
  const screenTarget = projectPoint(target, viewport)
  const { x1, y1, x2, y2 } = edgeEndpoints(screenSource, screenTarget)
  const { x: mx, y: my } = edgeMidpoint(screenSource, screenTarget)
  return { x1, y1, x2, y2, mx, my }
}

/** Bounding box (screen px) of a node's label + body for hit targets. */
export function nodeScreenBox(
  position: { x: number; y: number },
  viewport: NetworkViewport,
): { x: number; y: number; width: number; height: number } {
  const point = projectPoint(position, viewport)
  const radius = NODE_RADIUS * viewport.scale
  const labelWidth = 96 * viewport.scale
  const halfWidth = Math.max(radius, labelWidth / 2) + LABEL_PAD * viewport.scale
  const height = radius * 2 + 20 * viewport.scale
  return {
    x: point.x - halfWidth,
    y: point.y - radius,
    width: halfWidth * 2,
    height,
  }
}
