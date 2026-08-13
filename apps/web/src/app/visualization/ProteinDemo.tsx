'use client'

import { ProteinViewer } from '@/components/protein/ProteinViewer'
import { P53_PROTEIN_FIXTURE } from '@/lib/protein/protein.fixtures'
import { useProteinViewer } from '@/lib/protein/useProteinViewer'

/**
 * Phase 6.5 demo: Protein Viewer over the development fixture.
 *
 * The backend exposes protein identity + sequence, but not yet annotation
 * features, so this demo feeds the typed dev fixture through the same
 * normalizers the real adapter uses. See `docs/visualization/protein-viewer.md`.
 */
export function ProteinDemo() {
  const result = useProteinViewer({ loader: async () => P53_PROTEIN_FIXTURE })
  return <ProteinViewer result={result} />
}
