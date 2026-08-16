'use client'

import { useMemo } from 'react'

import { GeneTranscriptViewer } from '@/components/genome/GeneTranscriptViewer'
import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import type { GenomeViewport } from '@/lib/genome/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

export interface GeneTranscriptPanelProps {
  /** Shared context region the viewer renders around. */
  region: GenomeViewport
  dataSource: WorkspaceDataSource
}

/**
 * Gene / Transcript panel (Phase 6.9). Loads the gene overlapping the shared
 * context region through the Phase 6.1 data lifecycle and renders the existing
 * Phase 6.3 `GeneTranscriptViewer` at the same region. The panel is remounted
 * by the workspace whenever the context region changes so it always loads the
 * gene for the active region.
 */
export function GeneTranscriptPanel({ region, dataSource }: GeneTranscriptPanelProps) {
  const loader = useMemo(
    () => (signal: AbortSignal) => dataSource.loadGenes(region, signal),
    [dataSource, region],
  )

  const { status, data, error, refetch } = useVisualizationData(loader, {
    isEmpty: (genes) => genes.length === 0,
  })

  const gene = data?.[0]

  return (
    <VisualizationContainer
      title="Gene / Transcript Viewer"
      description="Gene span, transcript isoforms and exon blocks for the active research region."
      status={status}
      error={error}
      loadingLabel="Loading gene structure..."
      emptyMessage="No gene structure to show in this region."
      onRetry={refetch}
    >
      {status === 'success' && gene ? <GeneTranscriptViewer gene={gene} viewport={region} /> : null}
    </VisualizationContainer>
  )
}
