interface ChipProps {
  children: React.ReactNode
  tone?: 'default' | 'green' | 'amber' | 'red' | 'blue'
}

const tones: Record<NonNullable<ChipProps['tone']>, string> = {
  default: 'bg-slate-100 text-slate-700',
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-red-50 text-red-700 ring-red-200',
  blue: 'bg-genome-50 text-genome-700 ring-genome-200',
}

export function Chip({ children, tone = 'default' }: ChipProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  )
}
