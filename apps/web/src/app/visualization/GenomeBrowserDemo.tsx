'use client'

import { useMemo } from 'react'

import { GenomeBrowser } from '@/components/genome/GenomeBrowser'
import { fetchIntervalFeatures, fetchVariantFeatures } from '@/lib/genome/api'
import { TP53_WINDOW } from '@/lib/genome/geneTranscript.fixtures'
import type { GenomeTrackDefinition } from '@/lib/genome/useGenomeBrowser'

/**
 * Client-side Genome Browser demo (Phase 6.2).
 *
 * Wires the reusable `GenomeBrowser` to the real Phase 5 coordinate-search
 * API through the thin typed adapter in `lib/genome/api.ts`. It opens on
 * a chromosome 17 window (the TP53 neighbourhood) so it renders real data
 * without further user interaction.
 */
export function GenomeBrowserDemo() {
  const tracks = useMemo<GenomeTrackDefinition[]>(
    () => [
      {
        id: 'genes',
        label: 'Genes',
        kind: 'genes',
        loader: (interval, signal) => fetchIntervalFeatures('gene', interval, signal),
      },
      {
        id: 'variants',
        label: 'Variants',
        kind: 'variants',
        loader: (interval, signal) => fetchVariantFeatures(interval, signal),
      },
    ],
    [],
  )

  return <GenomeBrowser initialViewport={{ ...TP53_WINDOW }} tracks={tracks} />
}
