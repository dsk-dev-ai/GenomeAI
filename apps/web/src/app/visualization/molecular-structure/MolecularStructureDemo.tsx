'use client'

import { MolecularStructureViewer } from '@/components/molecular/MolecularStructureViewer'
import { P53_HELIX_STRUCTURE_FIXTURE } from '@/lib/molecular/molecular.fixtures'
import { useMolecularStructureViewer } from '@/lib/molecular/useMolecularStructureViewer'

/**
 * Phase 6.12 demo: Molecular Structure Viewer over the development fixture.
 *
 * The backend does not yet expose a molecular structure endpoint, so this
 * demo feeds the synthetic typed fixture through the same normalizer the
 * production adapter uses. See `docs/visualization/molecular-structure.md`.
 */
export function MolecularStructureDemo() {
  const result = useMolecularStructureViewer({
    loader: async () => P53_HELIX_STRUCTURE_FIXTURE,
  })
  return <MolecularStructureViewer result={result} />
}
