'use client'

import { CoverageChart } from '@/components/scientific/CoverageChart'
import { DistributionChart } from '@/components/scientific/DistributionChart'
import { ExpressionChart } from '@/components/scientific/ExpressionChart'
import { Heatmap } from '@/components/scientific/Heatmap'
import { VolcanoPlot } from '@/components/scientific/VolcanoPlot'
import { useCoverageChart } from '@/lib/scientific/useCoverageChart'
import { useDistributionChart } from '@/lib/scientific/useDistributionChart'
import { useExpressionChart } from '@/lib/scientific/useExpressionChart'
import { useHeatmap } from '@/lib/scientific/useHeatmap'
import { useVolcanoPlot } from '@/lib/scientific/useVolcanoPlot'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

export interface AnalysisChartPanelProps {
  dataSource: WorkspaceDataSource
}

/**
 * Analysis chart panels (Phase 6.9). Each reuses an existing Phase 6.7/6.8
 * chart hook + component unchanged, wired to the workspace data source. These
 * panels are whole-dataset fixtures (TP53-pathway analysis), so they do not
 * change when the genomic context region changes — see
 * `docs/visualization/workspace.md` for the fixture boundary.
 */

export function ExpressionPanel({ dataSource }: AnalysisChartPanelProps) {
  const result = useExpressionChart({ loader: dataSource.loadExpression })
  return <ExpressionChart result={result} title="Expression Chart" />
}

export function HeatmapPanel({ dataSource }: AnalysisChartPanelProps) {
  const result = useHeatmap({ loader: dataSource.loadHeatmap })
  return <Heatmap result={result} title="Expression Heatmap" />
}

export function VolcanoPanel({ dataSource }: AnalysisChartPanelProps) {
  const result = useVolcanoPlot({ loader: dataSource.loadVolcano })
  return <VolcanoPlot result={result} title="Volcano Plot" />
}

export function CoveragePanel({ dataSource }: AnalysisChartPanelProps) {
  const result = useCoverageChart({ loader: dataSource.loadCoverage, chromosome: 'chr17' })
  return <CoverageChart result={result} title="Coverage Chart" />
}

export function DistributionPanel({ dataSource }: AnalysisChartPanelProps) {
  const result = useDistributionChart({ loader: dataSource.loadDistribution })
  return <DistributionChart result={result} title="Distribution Chart" />
}
