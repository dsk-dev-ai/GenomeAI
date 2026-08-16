'use client'

import { useMemo } from 'react'

import { GenomeBrowser } from '@/components/genome/GenomeBrowser'
import { TP53_WINDOW } from '@/lib/genome/geneTranscript.fixtures'
import { fixtureIntervalGenes, fixtureIntervalVariants } from '@/lib/genome/genomeBrowser.fixtures'
import type { GenomeTrackDefinition } from '@/lib/genome/useGenomeBrowser'

/**
 * Client-side Genome Browser demo (Phase 6.2).
 *
 * Wires the reusable `GenomeBrowser` to typed development fixtures for the
 * TP53 neighbourhood (fixture-backed, like the other visualization demos)
 * until the Phase 5 coordinate-search backend is reachable. It opens on a
 * chromosome 17 window so it renders data without further user interaction.
 */
export function GenomeBrowserDemo() {
  const tracks = useMemo<GenomeTrackDefinition[]>(
    () => [
      {
        id: 'genes',
        label: 'Genes',
        kind: 'genes',
        loader: (interval, signal) => {
          void signal
          return Promise.resolve(fixtureIntervalGenes(interval))
        },
      },
      {
        id: 'variants',
        label: 'Variants',
        kind: 'variants',
        loader: (interval, signal) => {
          void signal
          return Promise.resolve(fixtureIntervalVariants(interval))
        },
      },
    ],
    [],
  )

  return <GenomeBrowser initialViewport={{ ...TP53_WINDOW }} tracks={tracks} />
}
