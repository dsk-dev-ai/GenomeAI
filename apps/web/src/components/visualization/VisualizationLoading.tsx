export interface VisualizationLoadingProps {
  /** Accessible label read aloud while loading. */
  label?: string
}

export function VisualizationLoading({ label = 'Loading...' }: VisualizationLoadingProps) {
  return (
    <output className="flex w-full items-center justify-center px-4 py-16">
      <span
        aria-hidden="true"
        className="size-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900"
      />
      <span className="ml-3 text-sm text-gray-700">{label}</span>
    </output>
  )
}
