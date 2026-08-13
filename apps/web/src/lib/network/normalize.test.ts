import { describe, expect, it } from 'vitest'

import { normalizeGraph, sortEdges, sortNodes } from './normalize'
import type { Graph } from './types'

const RAW_GRAPH: Graph = {
  id: 'g',
  nodes: [
    { id: 'b', label: 'B', type: 'gene' },
    { id: 'a', label: 'A', type: 'gene' },
    { id: 'b', label: 'B', type: 'gene' },
  ],
  edges: [
    { id: 'e2', source: 'b', target: 'c', type: 'x' },
    { id: 'e1', source: 'a', target: 'b', type: 'x' },
    { id: 'e3', source: 'a', target: 'a', type: 'y' },
    { id: 'e1', source: 'a', target: 'b', type: 'x' },
  ],
}

describe('normalizeGraph', () => {
  it('dedupes nodes and edges by id, keeping first occurrences', () => {
    const graph = normalizeGraph(RAW_GRAPH)
    expect(graph.nodes.map((node) => node.id)).toEqual(['a', 'b'])
    expect(graph.edges.filter((edge) => edge.id === 'e1')).toHaveLength(1)
  })

  it('drops self-loops and dangling edges', () => {
    const graph = normalizeGraph(RAW_GRAPH)
    expect(graph.edges.some((edge) => edge.source === edge.target)).toBe(false)
    expect(graph.edges.some((edge) => edge.target === 'c')).toBe(false)
  })

  it('orders nodes by id and edges by (source, target, type, id)', () => {
    const graph = normalizeGraph(RAW_GRAPH)
    expect(graph.nodes.map((node) => node.id)).toEqual(['a', 'b'])
    expect(graph.edges.map((edge) => edge.id)).toEqual(['e1'])
  })

  it('never mutates the input graph', () => {
    const graph = normalizeGraph(RAW_GRAPH)
    expect(RAW_GRAPH.nodes).toHaveLength(3)
    expect(RAW_GRAPH.edges).toHaveLength(4)
    expect(graph).not.toBe(RAW_GRAPH)
  })

  it('handles empty graphs', () => {
    const graph = normalizeGraph({ id: 'g', nodes: [], edges: [] })
    expect(graph.nodes).toEqual([])
    expect(graph.edges).toEqual([])
  })
})

describe('sortNodes / sortEdges', () => {
  it('sort without mutating inputs', () => {
    const nodes = [
      { id: 'b', label: 'B', type: 'gene' },
      { id: 'a', label: 'A', type: 'gene' },
    ]
    expect(sortNodes(nodes).map((node) => node.id)).toEqual(['a', 'b'])
    expect(nodes[0].id).toBe('b')

    const edges = [
      { id: 'e2', source: 'a', target: 'b', type: 'x' },
      { id: 'e1', source: 'a', target: 'a', type: 'x' },
    ]
    expect(sortEdges(edges).map((edge) => edge.id)).toEqual(['e1', 'e2'])
  })
})
