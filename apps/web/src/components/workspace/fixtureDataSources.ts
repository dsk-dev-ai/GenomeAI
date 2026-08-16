/**
 * Fixture-backed workspace data source (Phase 6.9).
 *
 * The demo workspace is wired to the clearly isolated dev fixtures, following
 * the same pattern as the Phase 6.2–6.8 demos: every loader resolves a typed
 * fixture and rejects with an `AbortError` once its signal aborts. Production
 * deployments swap this provider for the existing Phase 5 adapters
 * (`fetchGeneTranscripts`, `fetchIntervalFeatures`, `fetchVariants`,
 * `fetchNetworkGraph`, `fetchProtein`, `fetchExpressionDataset`,
 * `fetchHeatmapDataset`, ...) without changing the workspace UI. See
 * `docs/visualization/workspace.md` for the fixture boundary.
 */

import type { Gene } from '@/lib/genome/geneTranscript'
import { BRCA1_LIKE_FIXTURE, TP53_FIXTURE } from '@/lib/genome/geneTranscript.fixtures'
import { fixtureIntervalGenes, fixtureIntervalVariants } from '@/lib/genome/genomeBrowser.fixtures'
import type { GenomicInterval } from '@/lib/genome/types'
import { TP53_NETWORK_FIXTURE } from '@/lib/network/network.fixtures'
import { P53_PROTEIN_FIXTURE } from '@/lib/protein/protein.fixtures'
import {
  DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE,
  EXPRESSION_DISTRIBUTION_FIXTURE,
  TP53_PATHWAY_HEATMAP_FIXTURE,
  TP53_WINDOW_COVERAGE_FIXTURE,
} from '@/lib/scientific/advanced.fixtures'
import { TP53_PATHWAY_EXPRESSION_FIXTURE } from '@/lib/scientific/expression.fixtures'
import { type WorkspaceDataSource, resolveFixture } from '@/lib/workspace/dataSources'

/** The two gene-structure fixtures, filtered to those overlapping a region. */
function fixtureGenesForInterval(interval: GenomicInterval): Gene[] {
  return [TP53_FIXTURE, BRCA1_LIKE_FIXTURE].filter(
    (gene) =>
      gene.chromosome === interval.chromosome &&
      gene.start <= interval.end &&
      gene.end >= interval.start,
  )
}

function abortAware<T>(
  resolver: (signal: AbortSignal) => Promise<T>,
): (signal: AbortSignal) => Promise<T> {
  return (signal: AbortSignal): Promise<T> => {
    if (signal.aborted) {
      return Promise.reject(new DOMException('Aborted', 'AbortError'))
    }
    return resolver(signal)
  }
}

/** Default demo data source backed entirely by the Phase 6 dev fixtures. */
export const fixtureWorkspaceDataSource: WorkspaceDataSource = {
  loadGenes: (interval, signal) =>
    abortAware(() => Promise.resolve(fixtureGenesForInterval(interval)))(signal),
  loadGenomeGenes: (interval, signal) =>
    abortAware(() => Promise.resolve(fixtureIntervalGenes(interval)))(signal),
  loadGenomeVariants: (interval, signal) =>
    abortAware(() => Promise.resolve(fixtureIntervalVariants(interval)))(signal),
  loadNetwork: resolveFixture(TP53_NETWORK_FIXTURE),
  loadProtein: resolveFixture(P53_PROTEIN_FIXTURE),
  loadExpression: resolveFixture(TP53_PATHWAY_EXPRESSION_FIXTURE),
  loadHeatmap: resolveFixture(TP53_PATHWAY_HEATMAP_FIXTURE),
  loadVolcano: resolveFixture(DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE),
  loadCoverage: resolveFixture(TP53_WINDOW_COVERAGE_FIXTURE),
  loadDistribution: resolveFixture(EXPRESSION_DISTRIBUTION_FIXTURE),
}
