import type { VisualizationDataSource, VisualizationMetadata } from './types'

/**
 * Catalog of the visualization modules delivered across Phase 6.
 *
 * This started as a placeholder catalog for the Phase 6.1 foundation-only
 * demo. It now reflects the modules actually implemented in Phase 6.2–6.11, so
 * the demo catalog is an accurate map of the platform.
 */
export interface VisualizationModule extends VisualizationMetadata {
  source: VisualizationDataSource
  /** Roadmap milestone that delivered this module (e.g. `6.2`). */
  milestone: string
}

const MODULES: readonly VisualizationModule[] = [
  {
    id: 'genome-browser',
    title: 'Genome Browser',
    description: 'Chromosome-level navigation and feature tracks.',
    milestone: '6.2',
    source: { kind: 'api', reference: '/api/visualization/genomes' },
  },
  {
    id: 'gene-transcript-viewer',
    title: 'Gene / Transcript Viewer',
    description: 'Gene structure and isoform visualization.',
    milestone: '6.3',
    source: { kind: 'api', reference: '/api/visualization/genes' },
  },
  {
    id: 'variant-viewer',
    title: 'Variant Viewer',
    description: 'Variant context, consequence, and population data.',
    milestone: '6.4',
    source: { kind: 'api', reference: '/api/visualization/variants' },
  },
  {
    id: 'protein-viewer',
    title: 'Protein Viewer',
    description:
      'Protein sequence and annotation visualization: residue window, features, and selection.',
    milestone: '6.5',
    source: { kind: 'api', reference: '/api/visualization/proteins' },
  },
  {
    id: 'network-viewer',
    title: 'Biological Network Viewer',
    description:
      'Deterministic 2D relationship networks: typed graph model, layout, filtering, and selection.',
    milestone: '6.6',
    source: { kind: 'api', reference: '/api/visualization/networks' },
  },
  {
    id: 'scientific-charts',
    title: 'Scientific Charts',
    description:
      'Expression charts: reusable chart primitives, native scales, axes, tooltips, legends, and selection.',
    milestone: '6.7',
    source: { kind: 'api', reference: '/api/visualization/charts' },
  },
  {
    id: 'advanced-scientific-charts',
    title: 'Advanced Scientific Charts',
    description:
      'Expression heatmap, volcano plot, genomic coverage, and statistical distribution charts.',
    milestone: '6.8',
    source: { kind: 'api', reference: '/api/visualization/advanced-charts' },
  },
  {
    id: 'integrated-research-workspace',
    title: 'Integrated Research Workspace',
    description:
      'One research UI assembling the Phase 6.2–6.8 viewers around a shared genomic context.',
    milestone: '6.9',
    source: { kind: 'api', reference: '/api/visualization/workspace' },
  },
  {
    id: 'performance-large-datasets',
    title: 'Performance & Large-Dataset Handling',
    description:
      'Deterministic downsampling, aggregation, and per-render work reduction for large datasets.',
    milestone: '6.10',
    source: { kind: 'api', reference: '/api/visualization/performance' },
  },
  {
    id: 'testing-documentation',
    title: 'Testing & Documentation',
    description: 'Platform-wide coverage audit, edge-case tests, and reconciled documentation.',
    milestone: '6.11',
    source: { kind: 'api', reference: '/api/visualization/testing' },
  },
]

export interface FetchVisualizationModulesOptions {
  /** Simulated network latency in milliseconds. */
  delayMs?: number
  /** Thrown as the load error to exercise the error state. */
  failWith?: string
}

/**
 * Demo loader for the visualization module catalog.
 *
 * Resolves a typed list of `VisualizationModule`s after a short simulated
 * delay. This stands in for a future API endpoint — production callers will
 * replace it with a real GenomeAI API/SDK-backed loader while the component
 * and data-layer contracts stay the same.
 */
export function fetchVisualizationModules(
  signal: AbortSignal,
  options: FetchVisualizationModulesOptions = {},
): Promise<VisualizationModule[]> {
  const { delayMs = 500, failWith } = options

  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const timer = setTimeout(() => {
      if (failWith) {
        reject(new Error(failWith))
      } else {
        resolve([...MODULES])
      }
    }, delayMs)
    signal.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(new DOMException('Aborted', 'AbortError'))
    })
  })
}
