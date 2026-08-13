import { describe, expect, it } from 'vitest'

import {
  DEFAULT_NODE_COLOR,
  KNOWN_EDGE_TYPES,
  KNOWN_NODE_TYPES,
  edgeAccessibleLabel,
  edgeDetailLines,
  edgeLabel,
  edgeTypeColor,
  nodeAccessibleLabel,
  nodeDetailLines,
  nodeLabel,
  nodeTypeColor,
  typeLabel,
} from './labels'
import { TP53_NETWORK_FIXTURE } from './network.fixtures'

describe('nodeTypeColor', () => {
  it('maps known node types to stable colours', () => {
    expect(nodeTypeColor('gene')).toBe('#3b82f6')
    expect(nodeTypeColor('disease')).toBe('#ef4444')
    for (const type of KNOWN_NODE_TYPES) {
      expect(nodeTypeColor(type)).toMatch(/^#[0-9a-f]{6}$/)
    }
  })

  it('falls back for unknown types', () => {
    expect(nodeTypeColor('mystery_tag')).toBe(DEFAULT_NODE_COLOR)
  })
})

describe('edgeTypeColor', () => {
  it('maps known relationship types and falls back otherwise', () => {
    expect(edgeTypeColor('interacts_with')).toBe('#8b5cf6')
    for (const type of KNOWN_EDGE_TYPES) {
      expect(edgeTypeColor(type)).toMatch(/^#[0-9a-f]{6}$/)
    }
    expect(edgeTypeColor('unknown_relation')).toBe('#94a3b8')
  })
})

describe('typeLabel', () => {
  it('humanizes snake_case types', () => {
    expect(typeLabel('interacts_with')).toBe('interacts with')
    expect(typeLabel('gene')).toBe('gene')
  })
})

describe('node labels', () => {
  it('returns display and accessible labels', () => {
    const node = TP53_NETWORK_FIXTURE.nodes.find((candidate) => candidate.id === 'n-gene-tp53')
    expect(node).toBeDefined()
    if (node !== undefined) {
      expect(nodeLabel(node)).toBe('TP53')
      expect(nodeAccessibleLabel(node)).toBe('TP53, gene')
    }
  })
})

describe('edge labels', () => {
  it('prefers the relationship label over the type', () => {
    const edge = TP53_NETWORK_FIXTURE.edges.find((candidate) => candidate.id === 'e-tp53-p53')
    expect(edge).toBeDefined()
    if (edge !== undefined) {
      expect(edgeLabel(edge)).toBe('encodes')
      expect(edgeAccessibleLabel(edge, TP53_NETWORK_FIXTURE)).toBe('TP53 encodes P53')
    }
  })
})

describe('nodeDetailLines', () => {
  it('surfaces type, id, description, and metadata', () => {
    const node = TP53_NETWORK_FIXTURE.nodes.find((candidate) => candidate.id === 'n-gene-tp53')
    expect(node).toBeDefined()
    if (node !== undefined) {
      const lines = nodeDetailLines(node)
      const labels = lines.map((line) => line.label)
      expect(labels).toContain('Type')
      expect(labels).toContain('Identifier')
      expect(labels).toContain('Description')
    }
  })
})

describe('edgeDetailLines', () => {
  it('reports relationship, source, target, and direction', () => {
    const edge = TP53_NETWORK_FIXTURE.edges.find((candidate) => candidate.id === 'e-tp53-p53')
    expect(edge).toBeDefined()
    if (edge !== undefined) {
      const lines = edgeDetailLines(edge, TP53_NETWORK_FIXTURE)
      const byLabel = new Map(lines.map((line) => [line.label, line.value]))
      expect(byLabel.get('Relationship')).toBe('encodes')
      expect(byLabel.get('Source')).toBe('TP53')
      expect(byLabel.get('Target')).toBe('P53')
      expect(byLabel.get('Direction')).toBe('Directed')
    }
  })
})
