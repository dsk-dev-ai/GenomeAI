interface KeyValueProps {
  label: string
  value: React.ReactNode
}

export function KeyValue({ label, value }: KeyValueProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-sm font-medium text-slate-800">{value || '—'}</dd>
    </div>
  )
}

interface KeyValueGridProps {
  children: React.ReactNode
}

export function KeyValueGrid({ children }: KeyValueGridProps) {
  return <dl className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3">{children}</dl>
}
