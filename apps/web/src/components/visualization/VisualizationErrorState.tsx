import type { VisualizationError } from '@/lib/visualization/types'

export interface VisualizationErrorStateProps {
  error?: VisualizationError
  /** Accessible headline for the error state. */
  title?: string
  retryLabel?: string
  /** When provided, renders a keyboard-accessible retry button. */
  onRetry?: () => void
}

export function VisualizationErrorState({
  error,
  title = 'Failed to load visualization',
  retryLabel = 'Retry',
  onRetry,
}: VisualizationErrorStateProps) {
  return (
    <div
      className="flex w-full flex-col items-center justify-center px-4 py-16 text-center"
      role="alert"
    >
      <p className="text-sm font-semibold text-red-700">{title}</p>
      {error ? <p className="mt-2 max-w-md text-sm text-gray-600">{error.message}</p> : null}
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        >
          {retryLabel}
        </button>
      ) : null}
    </div>
  )
}
