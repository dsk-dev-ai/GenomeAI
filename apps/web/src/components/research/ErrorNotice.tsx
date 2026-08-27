interface ErrorNoticeProps {
  error: string | null
}

export function ErrorNotice({ error }: ErrorNoticeProps) {
  if (!error) return null
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {error}
    </div>
  )
}
