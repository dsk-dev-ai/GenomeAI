'use client'

import { NetworkViewer } from '@/components/network/NetworkViewer'
import { TP53_NETWORK_FIXTURE } from '@/lib/network/network.fixtures'
import { useNetworkViewer } from '@/lib/network/useNetworkViewer'

/**
 * Phase 6.6 demo: Biological Network Viewer over the development fixture.
 *
 * The backend does not yet expose a network endpoint, so this demo feeds a
 * typed dev fixture through the same normalizers the real adapter will use.
 * See `docs/visualization/network-viewer.md`.
 */
export function NetworkDemo() {
  const result = useNetworkViewer({ loader: async () => TP53_NETWORK_FIXTURE })
  return <NetworkViewer result={result} />
}
