import { type ReactNode, useId } from 'react'

import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { VisualizationEmpty } from './VisualizationEmpty'
import { VisualizationErrorState } from './VisualizationErrorState'
import { VisualizationLoading } from './VisualizationLoading'

export interface VisualizationContainerProps {
  /** Accessible container title, rendered as a secondary heading. */
  title: string
  /** Optional supporting text rendered beneath the title. */
  description?: string
  /** Data lifecycle status. `idle` is treated as `loading`. */
  status: VisualizationStatus
  /** Error details rendered when `status` is `error`. */
  error?: VisualizationError
  /** Message shown when `status` is `empty`. */
  emptyMessage?: string
  /** Accessible label shown while `status` is `loading`. */
  loadingLabel?: string
  /** Accessible headline rendered when `status` is `error`. */
  errorTitle?: string
  /** Renders a keyboard-accessible retry button in the error state. */
  onRetry?: () => void
  /** Content rendered when `status` is `success`. */
  children?: ReactNode
}

/**
 * Reusable container shared by every GenomeAI visualization. It owns the
 * surrounding semantics (heading, description) and renders exactly one of
 * the loading / empty / error / content states. It deliberately contains
 * no domain-specific visualization logic so future modules (genome
 * browser, gene/variant viewers, protein viewer, network viewer, charts)
 * can all build on the same foundation.
 */
export function VisualizationContainer({
  title,
  description,
  status,
  error,
  emptyMessage = 'No data available for this visualization.',
  loadingLabel = 'Loading...',
  errorTitle = 'Failed to load visualization',
  onRetry,
  children,
}: VisualizationContainerProps) {
  const titleId = useId()

  return (
    <section
      className="flex w-full flex-col rounded-lg border border-gray-200 bg-white p-4 sm:p-6"
      aria-labelledby={titleId}
    >
      <div className="flex w-full flex-col gap-1">
        <h2 id={titleId} className="text-lg font-semibold text-gray-900">
          {title}
        </h2>
        {description ? <p className="text-sm text-gray-600">{description}</p> : null}
      </div>
      <div className="mt-4 w-full flex-1 overflow-auto">
        {status === 'success' ? children : null}
        {status === 'loading' || status === 'idle' ? (
          <VisualizationLoading label={loadingLabel} />
        ) : null}
        {status === 'empty' ? <VisualizationEmpty message={emptyMessage} /> : null}
        {status === 'error' ? (
          <VisualizationErrorState error={error} title={errorTitle} onRetry={onRetry} />
        ) : null}
      </div>
    </section>
  )
}
