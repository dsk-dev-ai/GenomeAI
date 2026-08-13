import { afterEach, describe, expect, it, vi } from 'vitest'

import { GenomeApiError } from '@/lib/genome/api'

import { fetchNetworkGraph, graphFromRecords, toGraphEdge, toGraphNode } from './api'
import { isValidGraph } from './model'
import { TP53_NETWORK_FIXTURE } from './network.fixtures'

const rawFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = rawFetch
  vi.restoreAllMocks()
})

function jsonResponse(payload: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(payload),
  } as Response
}

describe('toGraphNode', () => {
  it('normalizes a raw node record', () => {
    const node = toGraphNode({
      id: 'n1',
      label: 'TP53',
      node_type: 'gene',
      description: 'Tumor suppressor',
      metadata: { evidence: 'curated' },
    })
    expect(node?.id).toBe('n1')
    expect(node?.label).toBe('TP53')
    expect(node?.type).toBe('gene')
    expect(node?.description).toBe('Tumor suppressor')
    expect(node?.metadata?.evidence).toBe('curated')
  })

  it('falls back to `type` and to the `custom` type', () => {
    expect(toGraphNode({ id: 'n1', label: 'X', type: 'protein' })?.type).toBe('protein')
    expect(toGraphNode({ id: 'n1', label: 'X' })?.type).toBe('custom')
  })

  it('drops records without an id or label', () => {
    expect(toGraphNode({ id: 'n1' })).toBeUndefined()
    expect(toGraphNode({ label: 'X' })).toBeUndefined()
    expect(toGraphNode(null)).toBeUndefined()
  })
})

describe('toGraphEdge', () => {
  it('normalizes a raw edge record', () => {
    const edge = toGraphEdge({
      id: 'e1',
      source: 'n1',
      target: 'n2',
      relationship: 'interacts_with',
      directed: true,
    })
    expect(edge?.source).toBe('n1')
    expect(edge?.target).toBe('n2')
    expect(edge?.type).toBe('interacts_with')
    expect(edge?.directed).toBe(true)
  })

  it('falls back to `type` and to `related_to`', () => {
    expect(toGraphEdge({ id: 'e1', source: 'a', target: 'b', type: 'regulates' })?.type).toBe(
      'regulates',
    )
    expect(toGraphEdge({ id: 'e1', source: 'a', target: 'b' })?.type).toBe('related_to')
  })

  it('drops records missing required fields', () => {
    expect(toGraphEdge({ id: 'e1', source: 'a' })).toBeUndefined()
    expect(toGraphEdge({ source: 'a', target: 'b' })).toBeUndefined()
  })
})

describe('graphFromRecords', () => {
  it('builds a normalized valid graph', () => {
    const graph = graphFromRecords({
      id: 'g1',
      title: 'Title',
      description: 'Desc',
      nodes: [{ id: 'a', label: 'A', node_type: 'gene' }],
      edges: [{ id: 'e', source: 'a', target: 'a', relationship: 'self' }],
    })
    expect(graph?.id).toBe('g1')
    expect(graph?.metadata?.title).toBe('Title')
    if (graph !== undefined) expect(isValidGraph(graph)).toBe(true)
    expect(graph?.edges).toHaveLength(0)
  })

  it('returns undefined for invalid records', () => {
    expect(graphFromRecords(null)).toBeUndefined()
    expect(graphFromRecords({ nodes: [], edges: [] })).toBeUndefined()
  })

  it('drops invalid nodes and dangling edges', () => {
    const graph = graphFromRecords({
      id: 'g1',
      nodes: [{ id: 'a', label: 'A', node_type: 'gene' }, { id: 'b' }],
      edges: [{ id: 'e', source: 'a', target: 'missing', relationship: 'x' }],
    })
    expect(graph?.nodes.map((node) => node.id)).toEqual(['a'])
    expect(graph?.edges).toEqual([])
  })
})

describe('fetchNetworkGraph', () => {
  it('GETs the network endpoint and normalizes the response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        id: 'network-tp53',
        nodes: [{ id: 'a', label: 'A', node_type: 'gene' }],
        edges: [],
      }),
    )
    globalThis.fetch = fetchMock as unknown as typeof fetch

    const { signal } = new AbortController()
    const graph = await fetchNetworkGraph('network-tp53', signal)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toContain('/networks/network-tp53')
    expect(init.signal).toBe(signal)
    expect(graph.id).toBe('network-tp53')
    expect(graph.nodes).toHaveLength(1)
  })

  it('throws a GenomeApiError on a non-2xx response', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 } as unknown as Response)
    await expect(fetchNetworkGraph('network-tp53')).rejects.toBeInstanceOf(GenomeApiError)
  })

  it('throws a GenomeApiError on a malformed payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(null))
    await expect(fetchNetworkGraph('network-tp53')).rejects.toBeInstanceOf(GenomeApiError)
  })
})

describe('fixture integrity', () => {
  it('fixture flows through the same normalizers', () => {
    expect(TP53_NETWORK_FIXTURE.id).toBe('network-tp53')
    expect(isValidGraph(TP53_NETWORK_FIXTURE)).toBe(true)
    expect(TP53_NETWORK_FIXTURE.nodes).toHaveLength(11)
    expect(TP53_NETWORK_FIXTURE.edges).toHaveLength(12)
  })
})
