import type { Metadata } from 'next'

import { ResearchWorkspace } from '@/components/workspace/ResearchWorkspace'

export const metadata: Metadata = {
  title: 'Research Workspace — GenomeAI',
  description:
    'Integrated research workspace (Phase 6.9): Genome Browser, Gene / Transcript viewer, Biological Network Viewer, Protein Viewer, and scientific / advanced scientific charts assembled around a shared genomic context.',
}

export default function ResearchWorkspacePage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-8">
      <div className="flex w-full flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Integrated Research Workspace</h1>
        <p className="text-sm text-gray-600">
          Assembles the Phase 6.2–6.8 visualization capabilities into one research UI (Phase 6.9).
          Pick a research context to drive the Genome Browser and the Gene / Transcript viewer; the
          network, protein, and analysis panels show the TP53-pathway datasets that support the
          workspace (fixture boundary — see the workspace documentation).
        </p>
      </div>
      <ResearchWorkspace />
    </main>
  )
}
