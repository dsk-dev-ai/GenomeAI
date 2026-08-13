import { describe, expect, it } from 'vitest'

import { filterGraph, isActiveFilter } from './filter'
import { TP53_NETWORK_FIXTURE } from './network.fixtures'
import type { GraphFilter } from './types'

describe('filterGraph', () => {
  it('returns the same graph for a null filter', () => {
    expect(filterGraph(TP53_NETWORK_FIXTURE, null)).toBe(TP53_NETWORK_FIXTURE)
  })

  it('keeps only nodes of the requested types', () => {
    const filter: GraphFilter = { nodeTypes: new Set(['gene']) }
    const filtered = filterGraph(TP53_NETWORK_FIXTURE, filter)
    expect(filtered.nodes.every((node) => node.type === 'gene')).toBe(true)
    expect(filtered.nodes).toHaveLength(4)
  })

  it('keeps only edges of the requested relationship types', () => {
    const filter: GraphFilter = { edgeTypes: new Set(['interacts_with']) }
    const filtered = filterGraph(TP53_NETWORK_FIXTURE, filter)
    expect(filtered.edges.every((edge) => edge.type === 'interacts_with')).toBe(true)
  })

  it('drops edges whose endpoints were filtered out (no dangling edges)', () => {
    const filter: GraphFilter = { nodeTypes: new Set(['gene', 'protein']) }
    const filtered = filterGraph(TP53_NETWORK_FIXTURE, filter)
    const nodeIds = new Set(filtered.nodes.map((node) => node.id))
    for (const edge of filtered.edges) {
      expect(nodeIds.has(edge.source)).toBe(true)
      expect(nodeIds.has(edge.target)).toBe(true)
    }
    // The gene-only edge e-tp53-mdm2 (gene->gene) survives node filtering.
    expect(filtered.edges.some((edge) => edge.id === 'e-tp53-mdm2')).toBe(true)
  })

  it('combines node and edge type filters', () => {
    const filter: GraphFilter = {
      nodeTypes: new Set(['drug', 'gene']),
      edgeTypes: new Set(['targets']),
    }
    const filtered = filterGraph(TP53_NETWORK_FIXTURE, filter)
    expect(filtered.nodes.map((node) => node.label).sort()).toEqual([
      'BRCA1',
      'CHEK2',
      'Cisplatin',
      'MDM2',
      'Nutlin-3a',
      'TP53',
    ])
    expect(filtered.edges.map((edge) => edge.id).sort()).toEqual([
      'e-cisplatin-tp53',
      'e-nutlin-mdm2',
    ])
  })

  it('returns an empty graph when nothing matches', () => {
    const filter: GraphFilter = { nodeTypes: new Set(['study']) }
    const filtered = filterGraph(TP53_NETWORK_FIXTURE, filter)
    expect(filtered.nodes).toEqual([])
    expect(filtered.edges).toEqual([])
  })

  it('never mutates the input graph', () => {
    const original = TP53_NETWORK_FIXTURE
    filterGraph(original, { nodeTypes: new Set(['gene']) })
    expect(original.nodes).toHaveLength(11)
    expect(original.edges).toHaveLength(12)
  })
})

describe('isActiveFilter', () => {
  it('is false for null and for empty sets', () => {
    expect(isActiveFilter(null)).toBe(false)
    expect(isActiveFilter({ nodeTypes: new Set() })).toBe(false)
    expect(isActiveFilter({ edgeTypes: new Set() })).toBe(false)
  })

  it('is true when any dimension restricts', () => {
    expect(isActiveFilter({ nodeTypes: new Set(['gene']) })).toBe(true)
    expect(isActiveFilter({ edgeTypes: new Set(['targets']) })).toBe(true)
  })
})
