'use client'

import { NetworkViewer } from '@/components/network/NetworkViewer'
import { useNetworkViewer } from '@/lib/network/useNetworkViewer'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

export interface NetworkPanelProps {
  dataSource: WorkspaceDataSource
}

/**
 * Biological Network panel (Phase 6.9). Reuses the Phase 6.6
 * `useNetworkViewer` hook and `NetworkViewer` component unchanged; the
 * relationship graph comes from the workspace data source. Network data is a
 * whole-dataset fixture, so this panel does not change when the genomic
 * context region changes.
 */
export function NetworkPanel({ dataSource }: NetworkPanelProps) {
  const result = useNetworkViewer({ loader: dataSource.loadNetwork })
  return <NetworkViewer result={result} title="Biological Network Viewer" />
}
