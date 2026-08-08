export interface VisualizationEmptyProps {
  /** Message shown when a visualization has no data to render. */
  message?: string
}

export function VisualizationEmpty({
  message = 'No data available for this visualization.',
}: VisualizationEmptyProps) {
  return (
    <div className="flex w-full items-center justify-center px-4 py-16 text-center">
      <p className="text-sm text-gray-600">{message}</p>
    </div>
  )
}
