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
 * Shows the module catalog flowing through the reusable
 * `VisualizationContainer`. The catalog maps the full Phase 6.2–6.12
 * platform, each entry resolving to the viewer(s) shown above on this page.
 */
export function VisualizationDemo() {
  const { status, data, error, refetch } = useVisualizationData(
    (signal) => fetchVisualizationModules(signal),
    { isEmpty: (modules) => modules.length === 0 },
  )

  return (
    <div className="flex w-full flex-col gap-6">
      <VisualizationContainer
        title="Delivered visualization modules"
        description="Foundation demo loading the visualization module catalog."
        status={status}
        error={error}
        loadingLabel="Loading visualization modules..."
        emptyMessage="No visualization modules are registered yet."
        onRetry={refetch}
      >
        <ul className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
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
    </div>
  )
}
