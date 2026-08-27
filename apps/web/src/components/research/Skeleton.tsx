interface SkeletonBlockProps {
  lines?: number
  className?: string
}

export function SkeletonBlock({ lines = 4, className = '' }: SkeletonBlockProps) {
  return (
    <div className={`space-y-3 ${className}`} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: static skeleton rows
        <div key={i} className="h-4 rounded-lg shimmer-bg" style={{ width: `${100 - i * 10}%` }} />
      ))}
    </div>
  )
}

export function ResultSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <div className="space-y-4" data-testid="result-skeleton">
      {Array.from({ length: cards }).map((_, i) => (
        <div
          // biome-ignore lint/suspicious/noArrayIndexKey: static skeleton cards
          key={i}
          className="animate-fade-in-up rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card"
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <div className="mb-4 h-5 w-1/3 rounded-lg shimmer-bg" />
          <SkeletonBlock lines={3} />
        </div>
      ))}
    </div>
  )
}
