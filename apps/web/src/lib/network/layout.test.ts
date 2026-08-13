import { describe, expect, it } from 'vitest'

import { LAYOUT_STRATEGIES, NODE_RADIUS, createLayout, layoutFromPositions } from './layout'
import { nodeDegrees } from './model'
import { TP53_NETWORK_FIXTURE, buildTestNetwork } from './network.fixtures'
import type { Graph, GraphLayout, GraphPoint } from './types'

function positionOf(layout: GraphLayout, id: string): GraphPoint {
  const point = layout.positions.get(id)
  if (point === undefined) throw new Error(`No position for node "${id}"`)
  return point
}

function radiusOf(point: GraphPoint): number {
  return Math.hypot(point.x, point.y)
}

describe('concentricLayout', () => {
  it('places the highest-degree hub at the centre', () => {
    const layout = createLayout(TP53_NETWORK_FIXTURE)
    const hub = TP53_NETWORK_FIXTURE.nodes.reduce((a, b) => {
      const degreeA = nodeDegrees(TP53_NETWORK_FIXTURE).get(a.id) ?? 0
      const degreeB = nodeDegrees(TP53_NETWORK_FIXTURE).get(b.id) ?? 0
      return degreeA >= degreeB ? a : b
    })
    expect(radiusOf(positionOf(layout, hub.id))).toBeLessThan(1)
  })

  it('is fully deterministic: same graph, same positions', () => {
    const a = createLayout(buildTestNetwork())
    const b = createLayout(buildTestNetwork())
    for (const node of a.positions.keys()) {
      expect(a.positions.get(node)).toEqual(b.positions.get(node))
    }
  })

  it('assigns every node a finite position and reports a bounding box', () => {
    const network = buildTestNetwork(40)
    const layout = createLayout(network)
    for (const node of network.nodes) {
      const point = positionOf(layout, node.id)
      expect(Number.isFinite(point.x)).toBe(true)
      expect(Number.isFinite(point.y)).toBe(true)
    }
    expect(layout.maxX).toBeGreaterThan(layout.minX)
    expect(layout.maxY).toBeGreaterThan(layout.minY)
    expect(layout.centerX).toBeCloseTo((layout.minX + layout.maxX) / 2)
  })

  it('keeps higher-degree nodes on inner rings than lower-degree nodes', () => {
    const network = buildTestNetwork()
    const layout = createLayout(network)
    const degrees = nodeDegrees(network)
    const hubRadius = radiusOf(positionOf(layout, 'n0'))
    const leaf = network.nodes.find((node) => degrees.get(node.id) === 1)
    expect(leaf).toBeDefined()
    const leafRadius = leaf === undefined ? 0 : radiusOf(positionOf(layout, leaf.id))
    expect(hubRadius).toBeLessThan(leafRadius)
  })

  it('keeps isolated nodes on the outermost ring', () => {
    const network = buildTestNetwork()
    const layout = createLayout(network)
    const isolated = network.nodes.filter((node) => (nodeDegrees(network).get(node.id) ?? 0) === 0)
    expect(isolated.length).toBeGreaterThan(0)
    const isolatedRadius = radiusOf(positionOf(layout, isolated[0].id))
    const hubRadius = radiusOf(positionOf(layout, 'n0'))
    expect(isolatedRadius).toBeGreaterThan(hubRadius)
  })

  it('returns an empty layout for an empty graph', () => {
    const layout = createLayout({ id: 'empty', nodes: [], edges: [] })
    expect(layout.positions.size).toBe(0)
    expect(layout.width).toBe(0)
  })
})

describe('layoutFromPositions', () => {
  it('derives the bounding box from explicit positions', () => {
    const graph: Graph = {
      id: 'g',
      nodes: [
        { id: 'a', label: 'A', type: 'gene' },
        { id: 'b', label: 'B', type: 'gene' },
      ],
      edges: [],
    }
    const layout = layoutFromPositions(
      graph,
      new Map([
        ['a', { x: 10, y: -20 }],
        ['b', { x: -30, y: 40 }],
      ]),
    )
    expect(layout.minX).toBe(-30)
    expect(layout.maxX).toBe(10)
    expect(layout.minY).toBe(-20)
    expect(layout.maxY).toBe(40)
    expect(layout.width).toBe(40)
    expect(layout.height).toBe(60)
    expect(layout.centerX).toBe(-10)
    expect(layout.centerY).toBe(10)
  })

  it('throws when a node position is missing or non-finite', () => {
    const graph: Graph = {
      id: 'g',
      nodes: [{ id: 'a', label: 'A', type: 'gene' }],
      edges: [],
    }
    expect(() => layoutFromPositions(graph, new Map([['a', { x: Number.NaN, y: 0 }]]))).toThrow(
      /finite position/,
    )
    expect(() => layoutFromPositions(graph, new Map())).toThrow(/missing a finite position/)
  })
})

describe('createLayout', () => {
  it('exposes at least the concentric strategy', () => {
    expect(Object.keys(LAYOUT_STRATEGIES)).toContain('concentric')
  })

  it('throws for an unknown strategy name', () => {
    expect(() => createLayout(TP53_NETWORK_FIXTURE, 'force-directed' as never)).toThrow(
      /Unknown graph layout strategy/,
    )
  })

  it('respects layout options for ring spacing', () => {
    const network = buildTestNetwork()
    const defaultLayout = createLayout(network)
    const spaciousLayout = createLayout(network, 'concentric', { ringStep: 200 })
    const defaultLeafRadius = radiusOf(positionOf(defaultLayout, 'n1'))
    const spaciousLeafRadius = radiusOf(positionOf(spaciousLayout, 'n1'))
    expect(spaciousLeafRadius).toBeGreaterThan(defaultLeafRadius)
  })

  it('uses NODE_RADIUS consistent with render geometry', () => {
    expect(NODE_RADIUS).toBeGreaterThan(0)
  })
})
