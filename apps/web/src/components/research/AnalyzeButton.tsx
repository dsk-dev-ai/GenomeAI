interface AnalyzeButtonProps {
  onClick: () => void
  loading: boolean
  disabled?: boolean
}

export function AnalyzeButton({ onClick, loading, disabled }: AnalyzeButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading || disabled}
      className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {loading ? 'Analyzing…' : 'Analyze'}
    </button>
  )
}
