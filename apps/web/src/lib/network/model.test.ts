import { describe, expect, it } from 'vitest'

import {
  availableEdgeTypes,
  availableNodeTypes,
  edgeById,
  edgesForNode,
  hasNode,
  isValidGraph,
  nodeById,
  nodeDegree,
  nodeDegrees,
} from './model'
import { TP53_NETWORK_FIXTURE, buildTestNetwork } from './network.fixtures'
import type { Graph } from './types'

describe('model lookups', () => {
  it('finds a node or edge by id', () => {
    const node = nodeById(TP53_NETWORK_FIXTURE, 'n-gene-tp53')
    expect(node?.label).toBe('TP53')
    expect(nodeById(TP53_NETWORK_FIXTURE, 'missing')).toBeUndefined()
    expect(edgeById(TP53_NETWORK_FIXTURE, 'e-tp53-p53')?.type).toBe('encodes')
    expect(edgeById(TP53_NETWORK_FIXTURE, 'missing')).toBeUndefined()
  })

  it('checks node membership', () => {
    expect(hasNode(TP53_NETWORK_FIXTURE, 'n-gene-tp53')).toBe(true)
    expect(hasNode(TP53_NETWORK_FIXTURE, 'missing')).toBe(false)
  })

  it('computes degree as an undirected count', () => {
    const degree = nodeDegree(TP53_NETWORK_FIXTURE, 'n-gene-tp53')
    expect(degree).toBe(9)
  })

  it('computes degrees for every node', () => {
    const degrees = nodeDegrees(TP53_NETWORK_FIXTURE)
    expect(degrees.get('n-gene-tp53')).toBe(9)
    expect(degrees.get('n-protein-p53')).toBe(2)
    expect(degrees.get('n-transcript-tp53')).toBe(1)
  })

  it('lists incident edges of a node', () => {
    const edges = edgesForNode(TP53_NETWORK_FIXTURE, 'n-protein-p53')
    expect(edges.map((edge) => edge.id).sort()).toEqual(['e-mdm2-p53', 'e-tp53-p53'])
  })

  it('derives sorted unique node and edge types', () => {
    expect(availableNodeTypes(TP53_NETWORK_FIXTURE)).toEqual([
      'disease',
      'drug',
      'gene',
      'protein',
      'transcript',
      'variant',
    ])
    expect(availableEdgeTypes(TP53_NETWORK_FIXTURE)).toEqual([
      'associated_with',
      'encodes',
      'has_variant',
      'interacts_with',
      'regulates',
      'targets',
      'transcribes',
    ])
  })
})

describe('isValidGraph', () => {
  it('accepts the normalized fixture', () => {
    expect(isValidGraph(TP53_NETWORK_FIXTURE)).toBe(true)
  })

  it('rejects empty ids, duplicate node ids, self-loops, and dangling edges', () => {
    const base: Graph = { id: '', nodes: [], edges: [] }
    expect(isValidGraph(base)).toBe(false) // empty id
    expect(
      isValidGraph({
        id: 'g',
        nodes: [{ id: 'a', label: 'A', type: 'gene' }],
        edges: [{ id: 'e', source: 'a', target: 'a', type: 'x' }],
      }),
    ).toBe(false)
    expect(
      isValidGraph({
        id: 'g',
        nodes: [{ id: 'a', label: 'A', type: 'gene' }],
        edges: [{ id: 'e', source: 'a', target: 'b', type: 'x' }],
      }),
    ).toBe(false)
    expect(
      isValidGraph({
        id: 'g',
        nodes: [
          { id: 'a', label: 'A', type: 'gene' },
          { id: 'a', label: 'A', type: 'gene' },
        ],
        edges: [],
      }),
    ).toBe(false)
  })

  it('accepts a valid small graph', () => {
    expect(
      isValidGraph({
        id: 'g',
        nodes: [
          { id: 'a', label: 'A', type: 'gene' },
          { id: 'b', label: 'B', type: 'gene' },
        ],
        edges: [{ id: 'e', source: 'a', target: 'b', type: 'interacts_with' }],
      }),
    ).toBe(true)
  })
})

describe('buildTestNetwork', () => {
  it('builds a valid star network with isolated nodes', () => {
    const network = buildTestNetwork()
    expect(isValidGraph(network)).toBe(true)
    expect(network.nodes).toHaveLength(30)
    // Star edges run n1..n27 -> n0 (nodeCount - 2 leaves, minus the two isolates).
    expect(nodeDegree(network, 'n0')).toBe(27)
    expect(nodeDegree(network, 'n28')).toBe(0)
    expect(nodeDegree(network, 'n29')).toBe(0)
  })
})
