import { describe, expect, it } from 'vitest'

import { BRCA1_LIKE_FIXTURE, TP53_FIXTURE } from '@/lib/genome/geneTranscript.fixtures'
import { TP53_NETWORK_FIXTURE } from '@/lib/network/network.fixtures'
import { P53_PROTEIN_FIXTURE } from '@/lib/protein/protein.fixtures'
import {
  DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE,
  EXPRESSION_DISTRIBUTION_FIXTURE,
  TP53_PATHWAY_HEATMAP_FIXTURE,
  TP53_WINDOW_COVERAGE_FIXTURE,
} from '@/lib/scientific/advanced.fixtures'
import { TP53_PATHWAY_EXPRESSION_FIXTURE } from '@/lib/scientific/expression.fixtures'

import { fixtureWorkspaceDataSource } from './fixtureDataSources'

const TP53_WINDOW = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }

describe('fixtureWorkspaceDataSource', () => {
  it('loads the TP53 gene for the TP53 window', async () => {
    const genes = await fixtureWorkspaceDataSource.loadGenes(
      TP53_WINDOW,
      new AbortController().signal,
    )
    expect(genes).toEqual([TP53_FIXTURE])
  })

  it('loads the BRCA1 gene for the BRCA1 locus', async () => {
    const genes = await fixtureWorkspaceDataSource.loadGenes(
      { chromosome: 'chr17', start: 43_044_295, end: 43_125_483 },
      new AbortController().signal,
    )
    expect(genes).toEqual([BRCA1_LIKE_FIXTURE])
  })

  it('returns no genes for a region without a fixture gene', async () => {
    const genes = await fixtureWorkspaceDataSource.loadGenes(
      { chromosome: 'chr1', start: 1, end: 1000 },
      new AbortController().signal,
    )
    expect(genes).toEqual([])
  })

  it('filters genome-browser genes and variants to the interval', async () => {
    const genes = await fixtureWorkspaceDataSource.loadGenomeGenes(
      TP53_WINDOW,
      new AbortController().signal,
    )
    expect(genes.some((feature) => feature.name === 'TP53')).toBe(true)
    const variants = await fixtureWorkspaceDataSource.loadGenomeVariants(
      TP53_WINDOW,
      new AbortController().signal,
    )
    expect(variants.some((feature) => feature.name === 'G>A')).toBe(true)
  })

  it('resolves every whole-dataset loader to its fixture', async () => {
    const signal = new AbortController().signal
    await expect(fixtureWorkspaceDataSource.loadNetwork(signal)).resolves.toBe(TP53_NETWORK_FIXTURE)
    await expect(fixtureWorkspaceDataSource.loadProtein(signal)).resolves.toBe(P53_PROTEIN_FIXTURE)
    await expect(fixtureWorkspaceDataSource.loadExpression(signal)).resolves.toBe(
      TP53_PATHWAY_EXPRESSION_FIXTURE,
    )
    await expect(fixtureWorkspaceDataSource.loadHeatmap(signal)).resolves.toBe(
      TP53_PATHWAY_HEATMAP_FIXTURE,
    )
    await expect(fixtureWorkspaceDataSource.loadVolcano(signal)).resolves.toBe(
      DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE,
    )
    await expect(fixtureWorkspaceDataSource.loadCoverage(signal)).resolves.toBe(
      TP53_WINDOW_COVERAGE_FIXTURE,
    )
    await expect(fixtureWorkspaceDataSource.loadDistribution(signal)).resolves.toBe(
      EXPRESSION_DISTRIBUTION_FIXTURE,
    )
  })

  it('rejects with an AbortError for an aborted signal', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(
      fixtureWorkspaceDataSource.loadGenes(TP53_WINDOW, controller.signal),
    ).rejects.toMatchObject({ name: 'AbortError' })
    await expect(
      fixtureWorkspaceDataSource.loadGenomeGenes(TP53_WINDOW, controller.signal),
    ).rejects.toMatchObject({ name: 'AbortError' })
    await expect(fixtureWorkspaceDataSource.loadNetwork(controller.signal)).rejects.toMatchObject({
      name: 'AbortError',
    })
  })
})
