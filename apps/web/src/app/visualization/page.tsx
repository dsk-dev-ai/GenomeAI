import type { Metadata } from 'next'
import Link from 'next/link'

import { AdvancedScientificDemo } from './AdvancedScientificDemo'
import { GeneTranscriptDemo } from './GeneTranscriptDemo'
import { GenomeBrowserDemo } from './GenomeBrowserDemo'
import { NetworkDemo } from './NetworkDemo'
import { ProteinDemo } from './ProteinDemo'
import { ScientificDemo } from './ScientificDemo'
import { VisualizationDemo } from './VisualizationDemo'

export const metadata: Metadata = {
  title: 'Visualization — GenomeAI',
  description:
    'Visualization foundation, Genome Browser, Gene / Transcript viewer, Variant track, Protein Viewer, Biological Network Viewer, Scientific Charts, Advanced Scientific Charts, and the Integrated Research Workspace (Phase 6.1–6.11) for GenomeAI.',
}

export default function VisualizationPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-8">
      <div className="flex w-full flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Visualization</h1>
        <p className="text-sm text-gray-600">
          Phase 6.1 foundation, the Phase 6.2 Genome Browser, the Phase 6.3 Gene / Transcript
          viewer, the Phase 6.4 Variant track, the Phase 6.5 Protein Viewer, the Phase 6.6
          Biological Network Viewer, the Phase 6.7 Scientific Charts, the Phase 6.8 Advanced
          Scientific Charts, the Phase 6.9 Integrated Research Workspace, the Phase 6.10 performance
          work, and the Phase 6.11 testing & documentation pass — region parsing, viewport
          navigation, track rendering, gene/transcript structure, point variants, protein sequence +
          annotation windows, deterministic relationship networks, expression charts, and heatmap /
          volcano / coverage / distribution charts over the GenomeAI API and development fixtures.
        </p>
      </div>
      <nav aria-label="Visualization pages" className="flex w-full flex-wrap gap-3">
        <Link
          href="/visualization/workspace"
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          Open Integrated Research Workspace
        </Link>
        <Link
          href="/visualization/molecular-structure"
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Open Molecular Structure Viewer
        </Link>
      </nav>
      <GenomeBrowserDemo />
      <GeneTranscriptDemo />
      <NetworkDemo />
      <ProteinDemo />
      <ScientificDemo />
      <AdvancedScientificDemo />
      <VisualizationDemo />
    </main>
  )
}
