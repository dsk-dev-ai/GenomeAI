import type { VisualizationDataSource, VisualizationMetadata } from './types'

/**
 * Placeholder catalog for the planned visualization modules.
 *
 * Phase 6.1 is foundation only — this data describes future modules so the
 * architecture (data flow through the visualization foundation) can be
 * demonstrated end to end. None of these modules are implemented yet.
 */
export interface VisualizationModule extends VisualizationMetadata {
  source: VisualizationDataSource
  /** Roadmap milestone that will deliver this module (e.g. `6.2`). */
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
    description: 'Statistical and research-oriented charts.',
    milestone: '6.7',
    source: { kind: 'api', reference: '/api/visualization/charts' },
  },
]

export interface FetchVisualizationModulesOptions {
  /** Simulated network latency in milliseconds. */
  delayMs?: number
  /** Thrown as the load error to exercise the error state. */
  failWith?: string
}

/**
 * Placeholder loader for the visualization module catalog.
 *
 * Resolves a typed list of `VisualizationModule`s after a short simulated
 * delay. This stands in for a future API endpoint — later milestones will
 * replace it with a real GenomeAI API/SDK-backed loader while the
 * component and data-layer contracts stay the same.
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
