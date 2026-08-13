import type { Metadata } from 'next'

import { GeneTranscriptDemo } from './GeneTranscriptDemo'
import { GenomeBrowserDemo } from './GenomeBrowserDemo'
import { NetworkDemo } from './NetworkDemo'
import { ProteinDemo } from './ProteinDemo'
import { VisualizationDemo } from './VisualizationDemo'

export const metadata: Metadata = {
  title: 'Visualization — GenomeAI',
  description:
    'Visualization foundation, Genome Browser, Gene / Transcript viewer, Variant track, Protein Viewer, and Biological Network Viewer (Phase 6.1–6.6) for GenomeAI.',
}

export default function VisualizationPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-8">
      <div className="flex w-full flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Visualization</h1>
        <p className="text-sm text-gray-600">
          Phase 6.1 foundation, the Phase 6.2 Genome Browser, the Phase 6.3 Gene / Transcript
          viewer, the Phase 6.4 Variant track, the Phase 6.5 Protein Viewer, and the Phase 6.6
          Biological Network Viewer — region parsing, viewport navigation, track rendering,
          gene/transcript structure, point variants, protein sequence + annotation windows, and
          deterministic relationship networks over the GenomeAI API and development fixtures.
        </p>
      </div>
      <GenomeBrowserDemo />
      <GeneTranscriptDemo />
      <NetworkDemo />
      <ProteinDemo />
      <VisualizationDemo />
    </main>
  )
}
