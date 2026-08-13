/**
 * 2D graph viewport (Phase 6.6).
 *
 * Pure pan/zoom/fit math for the Network Viewer. A `NetworkViewport` is a
 * screen-space translation `(x, y)` plus a zoom `scale`; a layout point `p`
 * projects to screen `(p.x * scale + x, p.y * scale + y)`. Mirroring the
 * genome/protein viewers, navigation is stateless: every operation returns a
 * new viewport. Fit-to-view is computed from the layout bounding box and a
 * target screen size.
 */

import type { GraphLayout, NetworkViewport } from './types'

/** Smallest zoom scale (maximum zoom-out). */
export const MIN_GRAPH_SCALE = 0.05

/** Largest zoom scale (maximum zoom-in). */
export const MAX_GRAPH_SCALE = 4

/** Default zoom scale for a fresh viewport. */
export const DEFAULT_GRAPH_SCALE = 1

/** Zoom factor applied per zoom step (mirrors the genome/protein viewers). */
export const ZOOM_FACTOR = 1.5

/** Padding (px) kept around the graph when fitting to view. */
export const FIT_PADDING = 40

/** A fresh viewport showing the layout at scale 1, translated to the origin. */
export function identityViewport(): NetworkViewport {
  return { x: 0, y: 0, scale: DEFAULT_GRAPH_SCALE }
}

/** Clamps a scale into the allowed range. */
export function clampGraphScale(scale: number): number {
  return Math.min(MAX_GRAPH_SCALE, Math.max(MIN_GRAPH_SCALE, scale))
}

/** Projects a layout point to screen coordinates under a viewport. */
export function projectPoint(
  point: { x: number; y: number },
  viewport: NetworkViewport,
): { x: number; y: number } {
  return {
    x: point.x * viewport.scale + viewport.x,
    y: point.y * viewport.scale + viewport.y,
  }
}

/** Pans the viewport by screen pixels. */
export function panViewport(viewport: NetworkViewport, dx: number, dy: number): NetworkViewport {
  if (!Number.isFinite(dx) || !Number.isFinite(dy)) return viewport
  return { ...viewport, x: viewport.x + dx, y: viewport.y + dy }
}

/**
 * Zooms around a screen point `(cx, cy)` (defaults to the origin). The
 * screen point under the cursor stays fixed while the scale changes.
 */
export function zoomViewport(
  viewport: NetworkViewport,
  factor: number,
  cx = 0,
  cy = 0,
): NetworkViewport {
  if (!Number.isFinite(factor) || factor <= 0) return viewport
  const scale = clampGraphScale(viewport.scale * factor)
  const ratio = scale / viewport.scale
  if (ratio === 1) return viewport
  return {
    scale,
    x: cx - (cx - viewport.x) * ratio,
    y: cy - (cy - viewport.y) * ratio,
  }
}

/**
 * Computes a viewport that fits the whole layout into a `width` x `height`
 * screen area, centred, with `FIT_PADDING` of breathing room.
 */
export function fitViewport(
  layout: GraphLayout,
  width: number,
  height: number,
  padding = FIT_PADDING,
): NetworkViewport {
  const usableWidth = Math.max(1, width - padding * 2)
  const usableHeight = Math.max(1, height - padding * 2)
  const layoutWidth = Math.max(1, layout.width)
  const layoutHeight = Math.max(1, layout.height)
  const scale = clampGraphScale(Math.min(usableWidth / layoutWidth, usableHeight / layoutHeight))
  return {
    scale,
    x: width / 2 - layout.centerX * scale,
    y: height / 2 - layout.centerY * scale,
  }
}
