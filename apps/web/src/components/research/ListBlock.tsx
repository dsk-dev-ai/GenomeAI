import type { ReactNode } from 'react'

export function ListBlock({
  items,
  empty = 'No data available',
  dense = false,
}: {
  items: ReactNode[]
  empty?: string
  dense?: boolean
}) {
  if (!items.length) {
    return <p className="text-sm text-slate-400">{empty}</p>
  }
  return (
    <ul className={dense ? 'space-y-1' : 'space-y-2.5'}>
      {items.map((item, i) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: items have no stable identifier
        <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-genome-500 to-indigo-400" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  )
}
