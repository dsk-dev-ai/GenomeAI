'use client'

import Link from 'next/link'

const features = [
  {
    emoji: '🧬',
    title: 'Gene Intelligence',
    desc: 'NCBI-driven gene annotations, function, variants and disease associations.',
    href: '/research/gene',
  },
  {
    emoji: '🧪',
    title: 'Variant Interpretation',
    desc: 'ACMG pathogenicity from ClinVar, gnomAD frequency and Ensembl VEP.',
    href: '/research/variant',
  },
  {
    emoji: '🔬',
    title: 'Protein Structure',
    desc: 'UniProt function with PDB and AlphaFold structural insights.',
    href: '/research/protein',
  },
  {
    emoji: '📚',
    title: 'Literature',
    desc: 'Europe PMC and Semantic Scholar biomedical research discovery.',
    href: '/research/literature',
  },
  {
    emoji: '💊',
    title: 'Drug Targets',
    desc: 'ChEMBL and PubChem compound and target exploration.',
    href: '/research/drug',
  },
  {
    emoji: '🛣️',
    title: 'Pathway & Network',
    desc: 'Reactome, STRING and KEGG biological pathway analysis.',
    href: '/research/pathway',
  },
  {
    emoji: '🩺',
    title: 'Disease',
    desc: 'OpenTargets, Disease Ontology and Monarch associations.',
    href: '/research/disease',
  },
  {
    emoji: '📊',
    title: 'Executive Report',
    desc: 'A unified multi-domain report across all seven analytic views.',
    href: '/research/report',
  },
]

const sources = [
  'NCBI',
  'Ensembl VEP',
  'UniProt',
  'ClinVar',
  'gnomAD',
  'PDB',
  'AlphaFold',
  'ChEMBL',
  'PubChem',
  'Reactome',
  'KEGG',
  'STRING',
  'OpenTargets',
  'Monarch',
  'Disease Ontology',
  'DGIdb',
  'Europe PMC',
  'Semantic Scholar',
  'Gemini AI',
]

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      {/* Animated background */}
      <div className="pointer-events-none absolute inset-0 -z-20 grid-pattern" />
      <div className="pointer-events-none absolute -top-32 left-1/4 -z-10 h-96 w-96 rounded-full bg-genome-200/50 blur-3xl animate-blob" />
      <div className="pointer-events-none absolute top-20 right-0 -z-10 h-80 w-80 rounded-full bg-indigo-300/40 blur-3xl animate-blob [animation-delay:-6s]" />
      <div className="pointer-events-none absolute bottom-0 left-0 -z-10 h-80 w-80 rounded-full bg-genome-300/30 blur-3xl animate-blob [animation-delay:-12s]" />

      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200/60 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-genome-500 to-genome-700 text-lg shadow-glow">
              🧬
            </span>
            <span className="text-lg font-bold tracking-tight text-slate-900">
              Genome<span className="text-gradient">AI</span>
            </span>
          </Link>
          <nav className="hidden items-center gap-2 md:flex">
            <a
              href="#features"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              Features
            </a>
            <a
              href="#sources"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              Data Sources
            </a>
            <Link
              href="/research"
              className="ml-2 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-genome-600 to-genome-500 px-5 py-2 text-sm font-semibold text-white shadow-glow transition hover:shadow-glow-lg hover:brightness-110"
            >
              Launch Research
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                aria-hidden="true"
              >
                <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
          </nav>
          <Link
            href="/research"
            className="inline-flex items-center rounded-xl bg-genome-600 px-4 py-2 text-sm font-semibold text-white md:hidden"
          >
            Launch
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 lg:grid-cols-2 lg:py-28">
        <div>
          <div className="animate-fade-in-up mb-6 inline-flex items-center gap-2 rounded-full border border-genome-200 bg-genome-50 px-4 py-1.5 text-xs font-semibold text-genome-700">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-genome-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-genome-500" />
            </span>
            Open-source · Zero cost · Free-tier AI
          </div>

          <h1 className="animate-fade-in-up [animation-delay:100ms] text-5xl font-extrabold leading-[1.05] tracking-tight text-slate-900 sm:text-6xl lg:text-7xl">
            Intelligence for the <span className="text-gradient">genome era</span>
          </h1>

          <p className="animate-fade-in-up [animation-delay:200ms] mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
            GenomeAI unifies{' '}
            <strong className="text-slate-800">18 free biological databases</strong> with free-tier
            Gemini AI to deliver gene, variant, protein, literature, drug, pathway and disease
            analysis — plus a single executive multi-domain report.
          </p>

          <div className="animate-fade-in-up [animation-delay:300ms] mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/research/report"
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-genome-600 to-genome-500 px-7 py-3 text-base font-semibold text-white shadow-glow transition hover:shadow-glow-lg hover:brightness-110"
            >
              Get an executive report
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className="transition-transform group-hover:translate-x-1"
                aria-hidden="true"
              >
                <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
            <Link
              href="/research"
              className="rounded-xl border border-slate-300 bg-white px-7 py-3 text-base font-semibold text-slate-700 transition hover:border-genome-300 hover:bg-genome-50 hover:text-genome-700"
            >
              Explore all tools
            </Link>
          </div>

          <div className="animate-fade-in-up [animation-delay:400ms] mt-10 flex flex-wrap gap-8">
            {[
              { value: '8', label: 'Analytic domains' },
              { value: '18', label: 'Free data APIs' },
              { value: '$0', label: 'Cost to run' },
              { value: '1', label: 'Unified report' },
            ].map((s) => (
              <div key={s.label}>
                <div className="text-3xl font-extrabold text-gradient">{s.value}</div>
                <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hero visual card */}
        <div className="animate-fade-in-up [animation-delay:200ms]">
          <div className="relative mx-auto max-w-md">
            <div className="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-br from-genome-400/30 to-indigo-400/20 blur-2xl" />
            <div className="glass animate-float rounded-[1.5rem] p-6 shadow-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-genome-600">
                    Executive Report
                  </p>
                  <p className="text-lg font-bold text-slate-900">BRCA1</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-genome-500 to-indigo-500 text-xl shadow-glow">
                  📊
                </span>
              </div>
              <div className="mt-4 space-y-3">
                {[
                  { label: 'Gene', val: 'DNA repair associated', pct: 100 },
                  { label: 'Variant', val: 'Pathogenic (ACMG)', pct: 88 },
                  { label: 'Protein', val: '6 PDB structures', pct: 75 },
                  { label: 'Disease', val: '9 associations', pct: 62 },
                ].map((row) => (
                  <div key={row.label} className="rounded-xl border border-slate-100 bg-white p-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-slate-700">{row.label}</span>
                      <span className="text-xs text-slate-400">{row.val}</span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-genome-500 to-indigo-400"
                        style={{ width: `${row.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between rounded-xl bg-slate-900 px-4 py-3">
                <span className="text-xs font-medium text-slate-300">AI Summary</span>
                <span className="flex h-2 w-2 gap-0.5">
                  <span className="h-full w-0.5 animate-pulse rounded bg-genome-300" />
                  <span className="h-full w-0.5 animate-pulse rounded bg-genome-300 [animation-delay:150ms]" />
                  <span className="h-full w-0.5 animate-pulse rounded bg-genome-300 [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-16">
        <div className="mb-12 text-center">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-genome-200 bg-genome-50 px-4 py-1.5 text-xs font-semibold text-genome-700">
            ✨ Eight domains, one platform
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            Everything a genomics researcher needs
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-slate-600">
            Every analysis combines authoritative, real, free biological data with AI-generated
            summaries.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((f, i) => (
            <Link
              key={f.title}
              href={f.href}
              className="group animate-fade-in-up rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-genome-200 hover:shadow-card-hover"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-genome-50 to-indigo-50 text-2xl transition-transform group-hover:scale-110">
                <span>{f.emoji}</span>
              </div>
              <h3 className="font-semibold text-slate-900">{f.title}</h3>
              <p className="mt-1 text-sm text-slate-500">{f.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Sources */}
      <section id="sources" className="border-t border-slate-200 bg-white/60 py-16">
        <div className="mx-auto max-w-7xl px-4">
          <div className="mb-10 text-center">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900">
              Powered by real, free data
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-slate-600">
              No mocks, no fake data — every result comes from authoritative public databases.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2.5">
            {sources.map((s, i) => (
              <span
                key={s}
                className="animate-fade-in-up inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-genome-300 hover:text-genome-700"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <span className="h-1.5 w-1.5 rounded-full bg-gradient-to-r from-genome-500 to-indigo-400" />
                {s}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-4 py-20">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-genome-600 via-genome-500 to-indigo-500 p-10 text-center shadow-glow-lg sm:p-16">
          <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <h2 className="relative text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Start exploring the genome today
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-genome-50">
            Free forever. Open-source. No credit card required.
          </p>
          <Link
            href="/research"
            className="relative mt-8 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-bold text-genome-700 shadow-lg transition hover:scale-105 hover:shadow-xl"
          >
            Enter the Research Console
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              aria-hidden="true"
            >
              <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-200 bg-white py-8">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="text-lg">🧬</span>
            <span className="font-bold text-slate-900">
              Genome<span className="text-gradient">AI</span>
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Open-source intelligence for the genome era · Zero cost · Free-tier AI
          </p>
        </div>
      </footer>
    </main>
  )
}
