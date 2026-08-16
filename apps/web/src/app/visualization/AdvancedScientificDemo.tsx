'use client'

import { CoverageChart } from '@/components/scientific/CoverageChart'
import { DistributionChart } from '@/components/scientific/DistributionChart'
import { Heatmap } from '@/components/scientific/Heatmap'
import { VolcanoPlot } from '@/components/scientific/VolcanoPlot'
import {
  DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE,
  EXPRESSION_DISTRIBUTION_FIXTURE,
  TP53_PATHWAY_HEATMAP_FIXTURE,
  TP53_WINDOW_COVERAGE_FIXTURE,
} from '@/lib/scientific/advanced.fixtures'
import { useCoverageChart } from '@/lib/scientific/useCoverageChart'
import { useDistributionChart } from '@/lib/scientific/useDistributionChart'
import { useHeatmap } from '@/lib/scientific/useHeatmap'
import { useVolcanoPlot } from '@/lib/scientific/useVolcanoPlot'

/**
 * Client-side demonstration of the Phase 6.8 Advanced Scientific Charts.
 *
 * Loads deterministic development fixtures (see
 * `lib/scientific/advanced.fixtures.ts`) through the same data lifecycle as a
 * production dataset. The fixtures are explicitly titled "fixture" and only
 * illustrate each chart's generic data model — the backend does not expose
 * heatmap, volcano, coverage, or distribution endpoints yet, so each loader
 * flips to its `fetch*Dataset` adapter once those endpoints exist.
 */

function resolveFixture<T>(fixture: T) {
  return (signal: AbortSignal): Promise<T> => {
    if (signal.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'))
    return Promise.resolve(fixture)
  }
}

function HeatmapDemo() {
  const result = useHeatmap({ loader: resolveFixture(TP53_PATHWAY_HEATMAP_FIXTURE) })
  return <Heatmap result={result} title="Expression Heatmap" />
}

function VolcanoDemo() {
  const result = useVolcanoPlot({
    loader: resolveFixture(DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE),
  })
  return <VolcanoPlot result={result} title="Volcano Plot" />
}

function CoverageDemo() {
  const result = useCoverageChart({
    loader: resolveFixture(TP53_WINDOW_COVERAGE_FIXTURE),
  })
  return <CoverageChart result={result} title="Coverage Chart" />
}

function DistributionDemo() {
  const result = useDistributionChart({
    loader: resolveFixture(EXPRESSION_DISTRIBUTION_FIXTURE),
  })
  return <DistributionChart result={result} title="Distribution Chart" />
}

export function AdvancedScientificDemo() {
  return (
    <section className="flex w-full flex-col gap-6" aria-label="Advanced scientific charts">
      <div className="flex w-full flex-col gap-2">
        <h2 className="text-xl font-semibold text-gray-900">Advanced Scientific Charts</h2>
        <p className="text-sm text-gray-600">
          Reusable scientific primitives built on the Phase 6.7 chart foundation: an expression
          heatmap, a volcano plot, a genomic coverage chart, and a statistical distribution chart.
          All demos are fixture-backed until the GenomeAI API exposes the corresponding endpoints.
        </p>
      </div>
      <div className="flex w-full flex-col gap-6">
        <HeatmapDemo />
        <VolcanoDemo />
        <CoverageDemo />
        <DistributionDemo />
      </div>
    </section>
  )
}
