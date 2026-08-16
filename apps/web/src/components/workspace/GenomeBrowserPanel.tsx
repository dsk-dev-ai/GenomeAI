'use client'

import { useMemo } from 'react'

import { GenomeBrowser } from '@/components/genome/GenomeBrowser'
import type { GenomeViewport } from '@/lib/genome/types'
import type { GenomeTrackDefinition } from '@/lib/genome/useGenomeBrowser'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

export interface GenomeBrowserPanelProps {
  /** Shared context region the browser opens on. */
  region: GenomeViewport
  dataSource: WorkspaceDataSource
}

/**
 * Genome Browser panel (Phase 6.9). Renders the existing Phase 6.2
 * `GenomeBrowser` with region-scoped gene + variant tracks sourced from the
 * workspace data source. The panel is remounted by the workspace whenever the
 * context region changes so the browser always opens on the shared region.
 */
export function GenomeBrowserPanel({ region, dataSource }: GenomeBrowserPanelProps) {
  const tracks = useMemo<GenomeTrackDefinition[]>(
    () => [
      {
        id: 'genes',
        label: 'Genes',
        kind: 'genes',
        loader: (interval, signal) => dataSource.loadGenomeGenes(interval, signal),
      },
      {
        id: 'variants',
        label: 'Variants',
        kind: 'variants',
        loader: (interval, signal) => dataSource.loadGenomeVariants(interval, signal),
      },
    ],
    [dataSource],
  )

  return (
    <section className="flex w-full flex-col rounded-lg border border-gray-200 bg-white p-4 sm:p-6">
      <div className="flex w-full flex-col gap-1">
        <h2 className="text-lg font-semibold text-gray-900">Genome Browser</h2>
        <p className="text-sm text-gray-600">
          Genes and variants across the active research region. Track loading stays viewport-scoped,
          so the browser always fetches only the visible interval.
        </p>
      </div>
      <div className="mt-4 w-full flex-1">
        <GenomeBrowser initialViewport={region} tracks={tracks} />
      </div>
    </section>
  )
}
