'use client'

import { ProteinViewer } from '@/components/protein/ProteinViewer'
import { useProteinViewer } from '@/lib/protein/useProteinViewer'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

export interface ProteinPanelProps {
  dataSource: WorkspaceDataSource
}

/**
 * Protein panel (Phase 6.9). Reuses the Phase 6.5 `useProteinViewer` hook and
 * `ProteinViewer` component unchanged; the protein record comes from the
 * workspace data source. Protein data is a whole-dataset fixture, so this
 * panel does not change when the genomic context region changes.
 */
export function ProteinPanel({ dataSource }: ProteinPanelProps) {
  const result = useProteinViewer({ loader: dataSource.loadProtein })
  return <ProteinViewer result={result} title="Protein Viewer" />
}
