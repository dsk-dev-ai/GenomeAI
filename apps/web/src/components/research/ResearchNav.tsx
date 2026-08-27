import Link from 'next/link'

const navItems = [
  { href: '/research', label: 'Overview' },
  { href: '/research/gene', label: 'Gene' },
  { href: '/research/variant', label: 'Variant' },
  { href: '/research/protein', label: 'Protein' },
  { href: '/research/literature', label: 'Literature' },
  { href: '/research/drug', label: 'Drug' },
  { href: '/research/pathway', label: 'Pathway' },
  { href: '/research/disease', label: 'Disease' },
  { href: '/research/report', label: 'Report' },
]

export function ResearchNav() {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex items-center gap-6">
          <Link href="/research" className="py-3 text-sm font-semibold text-gray-900">
            GenomeAI Research
          </Link>
          <div className="flex flex-wrap items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
