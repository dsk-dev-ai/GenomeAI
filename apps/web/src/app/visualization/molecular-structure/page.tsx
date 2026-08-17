import type { Metadata } from 'next'
import Link from 'next/link'

import { MolecularStructureDemo } from './MolecularStructureDemo'

export const metadata: Metadata = {
  title: 'Molecular Structure Viewer — GenomeAI',
  description:
    'Interactive 3D molecular structure viewer (Phase 6.12): cartoon, ball-and-stick, and space-filling representations over a synthetic development fixture.',
}

export default function MolecularStructurePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-8">
      <div className="flex w-full flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Molecular Structure Viewer</h1>
        <p className="text-sm text-gray-600">
          Phase 6.12 interactive 3D molecular structure rendering: orbit, zoom, and pan the camera;
          switch between cartoon / ribbon, ball-and-stick, and space-filling representations; and
          reset or fit the view. The demo renders a synthetic development fixture through the same
          typed normalizer the production structure adapter will use — no structure endpoint exists
          yet (see the molecular structure documentation).
        </p>
      </div>
      <nav aria-label="Visualization pages" className="flex w-full flex-wrap gap-3">
        <Link
          href="/visualization"
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          Back to Visualization
        </Link>
      </nav>
      <MolecularStructureDemo />
    </main>
  )
}
