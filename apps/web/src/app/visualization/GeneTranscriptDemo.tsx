'use client'

import { useMemo } from 'react'

import { GeneTranscriptViewer } from '@/components/genome/GeneTranscriptViewer'
import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import { TP53_FIXTURE } from '@/lib/genome/geneTranscript.fixtures'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

/**
 * Client-side Gene / Transcript demo (Phase 6.3).
 *
 * Renders the `GeneTranscriptViewer` inside the Phase 6.1
 * `VisualizationContainer`, demonstrating the full loading / success / empty
 * lifecycle over the fixture data. The viewer is positioned with the same
 * viewport convention as the Phase 6.2 Genome Browser (one-based inclusive
 * chr17 TP53 window), so the two visualizations stay coordinate-aligned when
 * placed on the same page.
 *
 * NOTE: exon structure currently comes from the isolated development fixture
 * (`lib/genome/geneTranscript.fixtures.ts`) because the Phase 5 API does not
 * yet expose exons. See `docs/visualization/gene-transcript.md`.
 */
export function GeneTranscriptDemo() {
  const viewport = useMemo(() => ({ chromosome: 'chr17', start: 7_660_000, end: 7_700_000 }), [])

  const { status, data, error, refetch } = useVisualizationData(async () => TP53_FIXTURE, {
    isEmpty: (gene) => gene.transcripts.length === 0,
  })

  return (
    <VisualizationContainer
      title="Gene / Transcript Viewer"
      description="Gene span, transcript isoforms, intron connectors and exon blocks (TP53, chr17)."
      status={status}
      error={error}
      loadingLabel="Loading gene structure..."
      emptyMessage="No gene structure to show in this region."
      onRetry={refetch}
    >
      {status === 'success' && data ? (
        <GeneTranscriptViewer gene={data} viewport={viewport} />
      ) : null}
    </VisualizationContainer>
  )
}
