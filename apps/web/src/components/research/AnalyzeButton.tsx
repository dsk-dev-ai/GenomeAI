interface AnalyzeButtonProps {
  onClick: () => void
  loading: boolean
  disabled?: boolean
  children?: React.ReactNode
}

export function AnalyzeButton({ onClick, loading, disabled, children }: AnalyzeButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading || disabled}
      className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-genome-600 to-genome-500 px-6 py-2.5 text-sm font-semibold text-white shadow-glow transition-all duration-200 hover:shadow-glow-lg hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
    >
      <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
      {loading ? (
        <>
          <svg
            className="h-4 w-4 animate-spin-slow"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
              className="opacity-25"
            />
            <path
              d="M22 12a10 10 0 0 1-10 10"
              stroke="currentColor"
              strokeWidth="4"
              strokeLinecap="round"
            />
          </svg>
          <span className="relative">Analyzing…</span>
        </>
      ) : (
        <span className="relative flex items-center gap-2">
          {children ?? 'Analyze'}
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            className="transition-transform group-hover:translate-x-0.5"
            aria-hidden="true"
          >
            <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
      )}
    </button>
  )
}
