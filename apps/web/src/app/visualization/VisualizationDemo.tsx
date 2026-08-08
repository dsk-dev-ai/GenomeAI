'use client'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'
import {
  type VisualizationModule,
  fetchVisualizationModules,
} from '@/lib/visualization/visualizationModules'

/**
 * Client-side demonstration of the Phase 6.1 visualization foundation.
 *
 * Shows the data lifecycle (loading → success / empty / error) flowing
 * through the reusable `VisualizationContainer`. The module catalog itself
 * is a placeholder — the individual visualizations arrive in later
 * milestones.
 */
export function VisualizationDemo() {
  const { status, data, error, refetch } = useVisualizationData(
    (signal) => fetchVisualizationModules(signal),
    { isEmpty: (modules) => modules.length === 0 },
  )

  return (
    <div className="grid w-full grid-cols-1 gap-6 lg:grid-cols-2">
      <VisualizationContainer
        title="Planned visualization modules"
        description="Foundation demo loading the visualization module catalog."
        status={status}
        error={error}
        loadingLabel="Loading visualization modules..."
        emptyMessage="No visualization modules are registered yet."
        onRetry={refetch}
      >
        <ul className="flex w-full flex-col gap-3">
          {(data ?? []).map((module: VisualizationModule) => (
            <li
              key={module.id}
              className="flex flex-col gap-1 rounded-md border border-gray-200 p-4"
            >
              <span className="text-sm font-medium text-gray-900">{module.title}</span>
              <span className="text-xs text-gray-600">{module.description}</span>
              <span className="text-xs text-gray-400">Phase {module.milestone}</span>
            </li>
          ))}
        </ul>
      </VisualizationContainer>

      <div className="flex w-full flex-col gap-6">
        <VisualizationContainer
          title="Empty state"
          status="empty"
          emptyMessage="No samples match the current selection."
        />
        <VisualizationContainer
          title="Error state"
          status="error"
          error={{ message: 'The visualization service could not be reached.' }}
          onRetry={() => undefined}
        />
      </div>
    </div>
  )
}
