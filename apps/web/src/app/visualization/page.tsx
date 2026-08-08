import type { Metadata } from 'next'

import { GenomeBrowserDemo } from './GenomeBrowserDemo'
import { VisualizationDemo } from './VisualizationDemo'

export const metadata: Metadata = {
  title: 'Visualization — GenomeAI',
  description: 'Visualization foundation and Genome Browser (Phase 6.1–6.2) for GenomeAI.',
}

export default function VisualizationPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-8">
      <div className="flex w-full flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Visualization</h1>
        <p className="text-sm text-gray-600">
          Phase 6.1 foundation and the Phase 6.2 Genome Browser — region parsing, viewport
          navigation, and track rendering over the coordinate-search API.
        </p>
      </div>
      <GenomeBrowserDemo />
      <VisualizationDemo />
    </main>
  )
}
