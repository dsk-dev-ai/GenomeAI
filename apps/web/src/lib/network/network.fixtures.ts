/**
 * Development fixtures for the Network Viewer (Phase 6.6).
 *
 * The GenomeAI backend does **not** yet expose a network endpoint, so this
 * module provides small, clearly isolated, typed fixtures that mimic what a
 * future relationship API would return. Records flow through the same
 * normalizers (`toGraphNode`, `toGraphEdge`, `graphFromRecords`) the real
 * adapter uses, so the seam is exercised exactly as production would.
 *
 * ## Boundary
 *
 * These are **development fixtures, not a real API** and not scientific fact.
 * The relationships below illustrate the viewer's generic node/edge model
 * (gene -> protein, protein -> disease, drug -> target, ...) and must be
 * replaced by real GenomeAI network data. See
 * `docs/visualization/network-viewer.md`.
 */

import { graphFromRecords } from './api'
import type { Graph } from './types'

/** Raw records for a small TP53-centred multi-type network. */
const TP53_NETWORK_RECORD = {
  id: 'network-tp53',
  title: 'TP53 interaction network',
  description: 'Illustrative gene/protein/disease/drug relationships around TP53 (fixture).',
  nodes: [
    { id: 'n-gene-tp53', label: 'TP53', node_type: 'gene', description: 'Tumor suppressor gene' },
    {
      id: 'n-protein-p53',
      label: 'P53',
      node_type: 'protein',
      description: 'Cellular tumor antigen p53',
    },
    {
      id: 'n-gene-mdm2',
      label: 'MDM2',
      node_type: 'gene',
      description: 'E3 ubiquitin-protein ligase',
    },
    {
      id: 'n-gene-brca1',
      label: 'BRCA1',
      node_type: 'gene',
      description: 'Breast cancer type 1 susceptibility protein',
    },
    {
      id: 'n-gene-chek2',
      label: 'CHEK2',
      node_type: 'gene',
      description: 'Serine/threonine-protein kinase',
    },
    {
      id: 'n-variant-r175h',
      label: 'R175H',
      node_type: 'variant',
      description: 'Pathogenic TP53 missense variant',
    },
    {
      id: 'n-disease-lung',
      label: 'Lung cancer',
      node_type: 'disease',
      description: 'Malignant lung neoplasm',
    },
    {
      id: 'n-disease-breast',
      label: 'Breast cancer',
      node_type: 'disease',
      description: 'Malignant breast neoplasm',
    },
    {
      id: 'n-drug-cisplatin',
      label: 'Cisplatin',
      node_type: 'drug',
      description: 'Platinum-based chemotherapy',
    },
    { id: 'n-drug-nutlin', label: 'Nutlin-3a', node_type: 'drug', description: 'MDM2 antagonist' },
    {
      id: 'n-transcript-tp53',
      label: 'TP53-201',
      node_type: 'transcript',
      description: 'Canonical p53 transcript',
    },
  ],
  edges: [
    {
      id: 'e-tp53-p53',
      source: 'n-gene-tp53',
      target: 'n-protein-p53',
      relationship: 'encodes',
      directed: true,
    },
    {
      id: 'e-tp53-transcript',
      source: 'n-gene-tp53',
      target: 'n-transcript-tp53',
      relationship: 'transcribes',
      directed: true,
    },
    {
      id: 'e-tp53-mdm2',
      source: 'n-gene-tp53',
      target: 'n-gene-mdm2',
      relationship: 'regulates',
      directed: true,
    },
    {
      id: 'e-mdm2-p53',
      source: 'n-gene-mdm2',
      target: 'n-protein-p53',
      relationship: 'interacts_with',
    },
    {
      id: 'e-tp53-brca1',
      source: 'n-gene-tp53',
      target: 'n-gene-brca1',
      relationship: 'interacts_with',
    },
    {
      id: 'e-tp53-chek2',
      source: 'n-gene-tp53',
      target: 'n-gene-chek2',
      relationship: 'regulates',
      directed: true,
    },
    {
      id: 'e-tp53-r175h',
      source: 'n-gene-tp53',
      target: 'n-variant-r175h',
      relationship: 'has_variant',
      directed: true,
    },
    {
      id: 'e-tp53-lung',
      source: 'n-gene-tp53',
      target: 'n-disease-lung',
      relationship: 'associated_with',
    },
    {
      id: 'e-tp53-breast',
      source: 'n-gene-tp53',
      target: 'n-disease-breast',
      relationship: 'associated_with',
    },
    {
      id: 'e-breast-brca1',
      source: 'n-disease-breast',
      target: 'n-gene-brca1',
      relationship: 'associated_with',
    },
    {
      id: 'e-cisplatin-tp53',
      source: 'n-drug-cisplatin',
      target: 'n-gene-tp53',
      relationship: 'targets',
      directed: true,
    },
    {
      id: 'e-nutlin-mdm2',
      source: 'n-drug-nutlin',
      target: 'n-gene-mdm2',
      relationship: 'targets',
      directed: true,
    },
  ],
}

/** TP53-centred multi-type network used by demos and tests. */
export const TP53_NETWORK_FIXTURE: Graph = graphFromRecords(TP53_NETWORK_RECORD) ?? {
  id: 'network-tp53',
  nodes: [],
  edges: [],
}

/**
 * A larger deterministic fixture for layout/perf tests: a star hub around
 * `n0`, a few cross edges, plus two isolated nodes. Every reference is
 * valid, so normalization keeps the graph intact.
 */
export function buildTestNetwork(nodeCount = 30, extraEdges = 4): Graph {
  const nodes = Array.from({ length: nodeCount }, (_, i) => ({
    id: `n${i}`,
    label: `Node ${i}`,
    type: i % 3 === 0 ? 'protein' : i % 3 === 1 ? 'gene' : 'disease',
  }))
  const edges: Array<{ id: string; source: string; target: string; type: string }> = []
  for (let i = 1; i < nodeCount - 2; i += 1) {
    edges.push({ id: `e-star-${i}`, source: `n${i}`, target: 'n0', type: 'regulates' })
  }
  for (let i = 0; i < Math.max(0, extraEdges); i += 1) {
    edges.push({
      id: `e-cross-${i}`,
      source: `n${i + 1}`,
      target: `n${nodeCount - 3 - i}`,
      type: 'interacts_with',
    })
  }
  return (
    graphFromRecords({ id: 'network-test', nodes, edges }) ?? {
      id: 'network-test',
      nodes: [],
      edges: [],
    }
  )
}
