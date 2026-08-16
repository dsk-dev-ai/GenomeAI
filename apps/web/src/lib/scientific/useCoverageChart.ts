/**
 * Coverage chart view-model hook (Phase 6.8).
 *
 * Composes the shared `useChartData` lifecycle with coverage derivation
 * (chromosome selection, coverage domain/extent) and genome viewport
 * navigation. The viewport logic is the same Phase 6.2 `GenomeViewport` used
 * by the Genome Browser (`lib/genome/viewport.ts`), so zoom/pan behavior is
 * shared rather than re-implemented per chart.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { GenomeViewport } from '@/lib/genome/types'
import { panViewport, zoomViewport } from '@/lib/genome/viewport'
import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { fetchCoverageDataset } from './advancedApi'
import type { CoverageDataset } from './advancedTypes'
import {
  type ValueDomain,
  coverageChromosomes,
  coverageDomain,
  coverageExtent,
  hasRenderableBins,
} from './coverage'
import { useChartData } from './useChartData'

/** Result shape of `useCoverageChart`, consumed by `CoverageChart`. */
export interface CoverageChartResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the dataset load request. */
  refetch: () => void
  /** Loaded dataset, or `undefined` until success. */
  dataset: CoverageDataset | undefined
  /** Chromosomes present in the dataset (sorted). */
  chromosomes: string[]
  /** The chromosome currently displayed. */
  chromosome: string
  /** Selects the chromosome to display. */
  selectChromosome: (chromosome: string) => void
  /** Coverage domain for the displayed chromosome, or `undefined`. */
  domain: ValueDomain | undefined
  /** Current viewport over the chromosome. */
  viewport: GenomeViewport | undefined
  /** Zooms the viewport by `factor` around its center. */
  zoom: (factor: number) => void
  /** Pans the viewport by `delta` bases. */
  pan: (delta: number) => void
  /** Resets the viewport to the full data extent. */
  resetViewport: () => void
}

export interface UseCoverageChartOptions {
  /** Fetches the dataset (defaults to `fetchCoverageDataset(datasetId)`). */
  loader?: (signal: AbortSignal) => Promise<CoverageDataset>
  /** Backend dataset id used when no custom loader is provided. */
  datasetId?: string
  /** Chromosome to display initially (defaults to the first, sorted). */
  chromosome?: string
}

export function useCoverageChart(options: UseCoverageChartOptions = {}): CoverageChartResult {
  const { datasetId } = options

  const { status, data, error, refetch } = useChartData<CoverageDataset>({
    loader: options.loader,
    datasetId,
    defaultLoader: fetchCoverageDataset,
    noLoaderMessage: 'No coverage dataset loader provided to useCoverageChart.',
    isEmpty: (dataset) => !hasRenderableBins(dataset),
  })

  const chromosomes = useMemo(() => (data === undefined ? [] : coverageChromosomes(data)), [data])

  const [chromosome, setChromosome] = useState<string | undefined>(options.chromosome)
  const [viewport, setViewport] = useState<GenomeViewport | undefined>(undefined)
  const lastViewportSourceRef = useRef<{ id: string; chromosome: string } | null>(null)

  // The active chromosome is derived from the user's selection (or option),
  // clamped to whatever the loaded dataset actually contains. Deriving it here
  // — instead of in an effect that writes state back — means a late-loading
  // effect can never overwrite a user's selection, and a dataset change falls
  // back to the first available chromosome automatically.
  const activeChromosome = useMemo(() => {
    if (data === undefined || chromosomes.length === 0) return undefined
    if (chromosome !== undefined && chromosomes.includes(chromosome)) return chromosome
    if (options.chromosome !== undefined && chromosomes.includes(options.chromosome)) {
      return options.chromosome
    }
    return chromosomes[0]
  }, [data, chromosomes, chromosome, options.chromosome])

  // Reset the viewport to the data extent only when the dataset or the active
  // chromosome actually changes. Re-running on every render (e.g. after a
  // zoom/pan) would otherwise undo the user's navigation.
  useEffect(() => {
    if (data === undefined || activeChromosome === undefined) return
    const source = { id: data.id, chromosome: activeChromosome }
    if (
      lastViewportSourceRef.current !== null &&
      lastViewportSourceRef.current.id === source.id &&
      lastViewportSourceRef.current.chromosome === source.chromosome
    ) {
      return
    }
    lastViewportSourceRef.current = source
    const extent = coverageExtent(data, activeChromosome)
    if (extent !== undefined) {
      setViewport({
        chromosome: activeChromosome,
        start: extent.start,
        end: extent.end,
        bounds: { length: extent.end },
      })
    }
  }, [data, activeChromosome])

  const dataset = data
  const domain = useMemo(
    () =>
      dataset === undefined || activeChromosome === undefined
        ? undefined
        : coverageDomain(dataset, activeChromosome),
    [dataset, activeChromosome],
  )

  const zoom = useCallback((factor: number) => {
    setViewport((current) => (current === undefined ? current : zoomViewport(current, factor)))
  }, [])

  const pan = useCallback((delta: number) => {
    setViewport((current) => (current === undefined ? current : panViewport(current, delta)))
  }, [])

  const resetViewport = useCallback(() => {
    if (data === undefined || activeChromosome === undefined) return
    const extent = coverageExtent(data, activeChromosome)
    if (extent === undefined) return
    setViewport({
      chromosome: activeChromosome,
      start: extent.start,
      end: extent.end,
      bounds: { length: extent.end },
    })
  }, [data, activeChromosome])

  const selectChromosome = useCallback((next: string) => {
    setChromosome(next)
  }, [])

  return {
    status,
    error,
    refetch,
    dataset,
    chromosomes,
    chromosome: activeChromosome ?? '',
    selectChromosome,
    domain,
    viewport,
    zoom,
    pan,
    resetViewport,
  }
}
