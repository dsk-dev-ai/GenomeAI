'use client'

import { useState } from 'react'

import type { GenomicInterval } from '@/lib/genome/types'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'
import {
  PRESET_CONTEXTS,
  type ResearchContext,
  contextRegionKey,
  customContextFromInterval,
} from '@/lib/workspace/researchContext'

import {
  CoveragePanel,
  DistributionPanel,
  ExpressionPanel,
  HeatmapPanel,
  VolcanoPanel,
} from './AnalysisChartPanels'
import { GeneTranscriptPanel } from './GeneTranscriptPanel'
import { GenomeBrowserPanel } from './GenomeBrowserPanel'
import { NetworkPanel } from './NetworkPanel'
import { ProteinPanel } from './ProteinPanel'
import { ResearchContextSelector } from './ResearchContextSelector'
import { fixtureWorkspaceDataSource } from './fixtureDataSources'

export interface ResearchWorkspaceProps {
  /** Injectable data source for tests; defaults to the fixture provider. */
  dataSource?: WorkspaceDataSource
  /** Preset contexts offered by the selector; defaults to the shared presets. */
  contexts?: readonly ResearchContext[]
}

/**
 * Integrated Research Workspace (Phase 6.9).
 *
 * Assembles the Phase 6.2–6.8 visualization capabilities around a shared
 * research context:
 *
 * - The context (preset or custom region) drives the Genome Browser and the
 *   Gene / Transcript viewer, which are remounted on every region change so
 *   they open on the same genomic coordinates.
 * - The Network, Protein and analysis chart panels reuse their existing
 *   hooks/components unchanged and keep their own local state (viewports,
 *   filters, selections) across context changes.
 *
 * Panel state stays local and predictable: only the region-driven panels react
 * to context changes, and each panel owns its own data lifecycle through the
 * shared `useVisualizationData` foundation.
 */
export function ResearchWorkspace({
  dataSource = fixtureWorkspaceDataSource,
  contexts = PRESET_CONTEXTS,
}: ResearchWorkspaceProps) {
  const [activeContext, setActiveContext] = useState<ResearchContext>(
    contexts[0] ?? PRESET_CONTEXTS[0],
  )

  function handleSelectContext(context: ResearchContext) {
    setActiveContext(context)
  }

  function handleNavigateRegion(interval: GenomicInterval) {
    setActiveContext(customContextFromInterval(interval))
  }

  const regionKey = contextRegionKey(activeContext.region)

  return (
    <div className="flex w-full flex-col gap-6">
      <ResearchContextSelector
        context={activeContext}
        contexts={contexts}
        onSelectContext={handleSelectContext}
        onNavigateRegion={handleNavigateRegion}
      />

      <div className="grid w-full grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <GenomeBrowserPanel
            key={regionKey}
            region={activeContext.region}
            dataSource={dataSource}
          />
        </div>
        <div className="lg:col-span-2">
          <GeneTranscriptPanel
            key={regionKey}
            region={activeContext.region}
            dataSource={dataSource}
          />
        </div>
        <NetworkPanel dataSource={dataSource} />
        <div className="lg:col-span-2">
          <ProteinPanel dataSource={dataSource} />
        </div>
        <ExpressionPanel dataSource={dataSource} />
        <HeatmapPanel dataSource={dataSource} />
        <VolcanoPanel dataSource={dataSource} />
        <CoveragePanel dataSource={dataSource} />
        <DistributionPanel dataSource={dataSource} />
      </div>
    </div>
  )
}
