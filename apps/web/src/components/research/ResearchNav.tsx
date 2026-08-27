'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

export const navItems = [
  { href: '/research', label: 'Overview', emoji: '🧬' },
  { href: '/research/gene', label: 'Gene', emoji: '🧬' },
  { href: '/research/variant', label: 'Variant', emoji: '🧪' },
  { href: '/research/protein', label: 'Protein', emoji: '🔬' },
  { href: '/research/literature', label: 'Literature', emoji: '📚' },
  { href: '/research/drug', label: 'Drug', emoji: '💊' },
  { href: '/research/pathway', label: 'Pathway', emoji: '🛣️' },
  { href: '/research/disease', label: 'Disease', emoji: '🩺' },
  { href: '/research/report', label: 'Report', emoji: '📊' },
]

export function ResearchNav() {
  const pathname = usePathname()
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const isActive = (href: string) =>
    href === '/research' ? pathname === href : pathname.startsWith(href)

  return (
    <header
      className={`sticky top-0 z-40 transition-all duration-300 ${
        scrolled
          ? 'border-b border-slate-200/70 bg-white/80 shadow-sm backdrop-blur-md'
          : 'border-b border-transparent bg-white'
      }`}
    >
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex h-16 items-center justify-between gap-6">
          <Link href="/" className="group flex items-center gap-2.5">
            <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-genome-500 to-genome-700 text-lg shadow-glow transition-transform group-hover:scale-105">
              <span className="text-white">🧬</span>
              <span className="absolute inset-0 -z-10 rounded-xl bg-genome-500 animate-pulse-ring" />
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              Genome<span className="text-gradient">AI</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`relative rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'bg-genome-50 text-genome-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                {item.label}
                {isActive(item.href) ? (
                  <span className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-gradient-to-r from-genome-500 to-indigo-400" />
                ) : null}
              </Link>
            ))}
          </nav>

          <button
            type="button"
            aria-label="Toggle menu"
            onClick={() => setOpen((v) => !v)}
            className="rounded-lg border border-slate-300 p-2 text-slate-700 hover:bg-slate-100 lg:hidden"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              aria-hidden="true"
            >
              {open ? (
                <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" />
              ) : (
                <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-slate-200 bg-white px-4 pb-4 pt-2 lg:hidden">
          <div className="grid grid-cols-2 gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive(item.href)
                    ? 'bg-genome-50 text-genome-700'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span className="mr-1.5">{item.emoji}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </header>
  )
}
