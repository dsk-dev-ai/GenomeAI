import { describe, expect, it } from 'vitest'

import { edgeEndpoints, edgeMidpoint, edgeScreenPoints, nodeScreenBox } from './geometry'
import { createLayout } from './layout'
import { NODE_RADIUS } from './layout'
import { buildTestNetwork } from './network.fixtures'

describe('edgeEndpoints', () => {
  it('shortens the line by the node radius on both ends', () => {
    const result = edgeEndpoints({ x: 0, y: 0 }, { x: 100, y: 0 })
    expect(result.x1).toBeCloseTo(NODE_RADIUS + 2)
    expect(result.x2).toBeCloseTo(100 - (NODE_RADIUS + 2))
    expect(result.y1).toBe(0)
    expect(result.y2).toBe(0)
  })

  it('keeps points intact for coincident endpoints', () => {
    const result = edgeEndpoints({ x: 5, y: 5 }, { x: 5, y: 5 })
    expect(result).toEqual({ x1: 5, y1: 5, x2: 5, y2: 5 })
  })
})

describe('edgeMidpoint', () => {
  it('returns the arithmetic midpoint', () => {
    expect(edgeMidpoint({ x: 0, y: 0 }, { x: 10, y: 20 })).toEqual({ x: 5, y: 10 })
  })
})

describe('edgeScreenPoints', () => {
  it('projects endpoints through the viewport and returns a midpoint', () => {
    const graph = buildTestNetwork(6, 0)
    const layout = createLayout(graph)
    const viewport = { x: 0, y: 0, scale: 1 }
    const edge = graph.edges[0]
    const points = edgeScreenPoints(edge, layout, viewport)
    const source = layout.positions.get(edge.source)
    const target = layout.positions.get(edge.target)
    expect(source).toBeDefined()
    expect(target).toBeDefined()
    if (source !== undefined && target !== undefined) {
      expect(points.mx).toBeCloseTo((source.x + target.x) / 2)
      expect(points.my).toBeCloseTo((source.y + target.y) / 2)
    }
  })

  it('returns zeros for a dangling edge', () => {
    const layout = createLayout({ id: 'g', nodes: [], edges: [] })
    const points = edgeScreenPoints({ id: 'e', source: 'a', target: 'b', type: 'x' }, layout, {
      x: 0,
      y: 0,
      scale: 1,
    })
    expect(points).toEqual({ x1: 0, y1: 0, x2: 0, y2: 0, mx: 0, my: 0 })
  })
})

describe('nodeScreenBox', () => {
  it('centres the box on the projected node position', () => {
    const viewport = { x: 0, y: 0, scale: 1 }
    const box = nodeScreenBox({ x: 100, y: 50 }, viewport)
    expect(box.x + box.width / 2).toBeCloseTo(100)
    expect(box.height).toBeGreaterThan(NODE_RADIUS * 2)
  })

  it('scales with the viewport zoom', () => {
    const box1 = nodeScreenBox({ x: 0, y: 0 }, { x: 0, y: 0, scale: 1 })
    const box2 = nodeScreenBox({ x: 0, y: 0 }, { x: 0, y: 0, scale: 2 })
    expect(box2.width).toBeCloseTo(box1.width * 2)
  })
})
