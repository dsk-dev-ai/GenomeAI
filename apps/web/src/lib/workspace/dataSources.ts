/**
 * Workspace data-source seam (Phase 6.9).
 *
 * Workspace panels never load data directly: each receives a
 * `WorkspaceDataSource` whose loaders follow the existing shapes — the Phase
 * 6.1 `VisualizationLoader` contract (`(signal) => Promise<T>`) for whole
 * datasets, and the Phase 6.2 genome-track loader contract
 * (`(interval, signal) => Promise<T[]>`) for region-scoped data. This keeps
 * panel state local and predictable, lets tests inject empty/failing loaders
 * deterministically, and lets a production deployment swap the fixture
 * provider (`components/workspace/fixtureDataSources.ts`) for the existing
 * Phase 5 adapters without touching the workspace UI.
 */

import type { Gene } from '@/lib/genome/geneTranscript'
import type { GenomicFeature, GenomicInterval, VariantFeature } from '@/lib/genome/types'
import type { Graph } from '@/lib/network/types'
import type { Protein } from '@/lib/protein/types'
import type {
  CoverageDataset,
  DistributionDataset,
  HeatmapDataset,
  VolcanoDataset,
} from '@/lib/scientific/advancedTypes'
import type { ExpressionDataset } from '@/lib/scientific/types'

/** Loader shape matching the Phase 6.1 `useVisualizationData` lifecycle. */
export type WorkspaceLoader<T> = (signal: AbortSignal) => Promise<T>

/** Region-scoped loader shape matching `lib/genome/useGenomeBrowser`. */
export type WorkspaceIntervalLoader<T> = (
  interval: GenomicInterval,
  signal: AbortSignal,
) => Promise<T[]>

/** Every data source the workspace panels need, keyed by responsibility. */
export interface WorkspaceDataSource {
  /** Gene / transcript records overlapping a region. */
  loadGenes: WorkspaceIntervalLoader<Gene>
  /** Genome-browser gene spans for a region. */
  loadGenomeGenes: WorkspaceIntervalLoader<GenomicFeature>
  /** Genome-browser variant marks for a region. */
  loadGenomeVariants: WorkspaceIntervalLoader<VariantFeature>
  /** Biological relationship network for the research context. */
  loadNetwork: WorkspaceLoader<Graph>
  /** Protein record (sequence + annotation features). */
  loadProtein: WorkspaceLoader<Protein>
  /** Gene-expression dataset. */
  loadExpression: WorkspaceLoader<ExpressionDataset>
  /** Expression heatmap dataset. */
  loadHeatmap: WorkspaceLoader<HeatmapDataset>
  /** Differential-expression volcano dataset. */
  loadVolcano: WorkspaceLoader<VolcanoDataset>
  /** Read-depth coverage dataset. */
  loadCoverage: WorkspaceLoader<CoverageDataset>
  /** Statistical distribution dataset. */
  loadDistribution: WorkspaceLoader<DistributionDataset>
}

/**
 * Resolves a constant fixture through the loader contract, rejecting with an
 * `AbortError` once the signal has aborted. Mirrors the demo loader pattern
 * (`resolveFixture` in the Phase 6.7/6.8 demos) so fixtures honour the shared
 * cancellation contract.
 */
export function resolveFixture<T>(fixture: T): WorkspaceLoader<T> {
  return (signal: AbortSignal): Promise<T> => {
    if (signal.aborted) {
      return Promise.reject(new DOMException('Aborted', 'AbortError'))
    }
    return Promise.resolve(fixture)
  }
}
