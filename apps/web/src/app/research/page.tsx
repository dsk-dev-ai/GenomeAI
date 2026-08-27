'use client'

import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import Link from 'next/link'

const domains = [
  {
    href: '/research/gene',
    title: 'Gene',
    icon: '🧬',
    desc: 'NCBI gene annotations + function',
    accent: 'from-genome-500 to-genome-700',
  },
  {
    href: '/research/variant',
    title: 'Variant',
    icon: '🧪',
    desc: 'ClinVar + gnomAD + VEP pathogenicity',
    accent: 'from-violet-500 to-purple-700',
  },
  {
    href: '/research/protein',
    title: 'Protein',
    icon: '🔬',
    desc: 'UniProt + PDB + AlphaFold structure',
    accent: 'from-sky-500 to-blue-700',
  },
  {
    href: '/research/literature',
    title: 'Literature',
    icon: '📚',
    desc: 'Europe PMC + Semantic Scholar papers',
    accent: 'from-amber-500 to-orange-600',
  },
  {
    href: '/research/drug',
    title: 'Drug',
    icon: '💊',
    desc: 'ChEMBL + PubChem drug targets',
    accent: 'from-emerald-500 to-teal-700',
  },
  {
    href: '/research/pathway',
    title: 'Pathway',
    icon: '🛣️',
    desc: 'Reactome + STRING + KEGG pathways',
    accent: 'from-rose-500 to-pink-700',
  },
  {
    href: '/research/disease',
    title: 'Disease',
    icon: '🩺',
    desc: 'OpenTargets + DO + Monarch',
    accent: 'from-indigo-500 to-violet-700',
  },
  {
    href: '/research/report',
    title: 'Report',
    icon: '📊',
    desc: 'Multi-domain executive summary',
    accent: 'from-slate-700 to-slate-900',
  },
]

const stats = [
  { value: '18+', label: 'Free data APIs' },
  { value: '21', label: 'Data sources' },
  { value: '8', label: 'Analytic domains' },
  { value: '$0', label: 'Cost to run' },
]

export default function ResearchHome() {
  return (
    <>
      <ResearchNav />
      <main className="relative min-h-screen overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 grid-pattern" />
        <div className="pointer-events-none absolute -top-24 right-0 -z-10 h-80 w-80 rounded-full bg-genome-200/40 blur-3xl animate-blob" />
        <div className="pointer-events-none absolute bottom-0 left-0 -z-10 h-80 w-80 rounded-full bg-indigo-200/30 blur-3xl animate-blob [animation-delay:-8s]" />

        <div className="mx-auto max-w-7xl px-4 py-16">
          <Reveal>
            <header className="text-center">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-genome-200 bg-genome-50 px-4 py-1.5 text-xs font-semibold text-genome-700">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-genome-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-genome-500" />
                </span>
                21 free data APIs · Free-tier Gemini AI · Zero cost
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
                GenomeAI <span className="text-gradient">Research Console</span>
              </h1>
              <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
                Explore every analytic domain with real, free biological data — from raw gene
                annotations to a unified executive report.
              </p>
            </header>
          </Reveal>

          <Reveal delay={120}>
            <div className="mx-auto mt-10 flex max-w-3xl flex-wrap justify-center gap-6">
              {stats.map((s) => (
                <div key={s.label} className="text-center">
                  <div className="text-3xl font-extrabold text-gradient">{s.value}</div>
                  <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    {s.label}
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {domains.map((d, i) => (
              <Reveal key={d.href} delay={i * 60}>
                <Link
                  href={d.href}
                  className="group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-card-hover"
                >
                  <div
                    className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-2xl text-white shadow-lg transition-transform group-hover:scale-110 ${d.accent}`}
                  >
                    {d.icon}
                  </div>
                  <h2 className="font-semibold text-slate-900 group-hover:text-genome-700">
                    {d.title}
                  </h2>
                  <p className="mt-1 flex-1 text-sm text-slate-500">{d.desc}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-genome-600 opacity-0 transition-opacity group-hover:opacity-100">
                    Open
                    <span className="transition-transform group-hover:translate-x-0.5">→</span>
                  </span>
                </Link>
              </Reveal>
            ))}
          </div>
        </div>
      </main>
    </>
  )
}
