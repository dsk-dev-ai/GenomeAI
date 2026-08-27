interface ErrorNoticeProps {
  error: string | null
}

export function ErrorNotice({ error }: ErrorNoticeProps) {
  if (!error) return null
  return (
    <div className="animate-fade-in-down mb-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          aria-hidden="true"
        >
          <path d="M12 9v4M12 17h.01" strokeLinecap="round" />
        </svg>
      </span>
      <span>{error}</span>
    </div>
  )
}
