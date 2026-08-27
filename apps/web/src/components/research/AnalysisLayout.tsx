import { Reveal } from './Reveal'

interface AnalysisLayoutProps {
  title: string
  subtitle?: string
  icon?: string
  accent?: string
  children: React.ReactNode
}

export function AnalysisLayout({
  title,
  subtitle,
  icon,
  accent = 'from-genome-500 to-indigo-400',
  children,
}: AnalysisLayoutProps) {
  return (
    <main className="relative min-h-[calc(100vh-4rem)] overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-72 bg-gradient-to-b from-white to-transparent" />
      <div className="pointer-events-none absolute -right-24 -top-24 -z-10 h-72 w-72 rounded-full bg-genome-200/40 blur-3xl animate-blob" />
      <div className="pointer-events-none absolute -left-24 top-40 -z-10 h-64 w-64 rounded-full bg-indigo-200/30 blur-3xl animate-blob [animation-delay:-6s]" />

      <div className="mx-auto max-w-7xl px-4 py-12">
        <Reveal>
          <header className="mb-10">
            <div className="mb-4 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-genome-600">
              <span className="h-px w-8 bg-gradient-to-r from-genome-500 to-transparent" />
              GenomeAI Research
            </div>
            <div className="flex items-center gap-4">
              {icon ? (
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-genome-500 to-indigo-500 text-2xl shadow-glow">
                  <span className="grayscale-[20%]">{icon}</span>
                </span>
              ) : null}
              <h1
                className={`bg-gradient-to-r bg-clip-text text-4xl font-extrabold tracking-tight text-transparent sm:text-5xl ${accent}`}
              >
                {title}
              </h1>
            </div>
            {subtitle ? (
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-slate-500 sm:text-base">
                {subtitle}
              </p>
            ) : null}
          </header>
        </Reveal>
        <div className="animate-fade-in-up [animation-delay:120ms]">{children}</div>
      </div>
    </main>
  )
}
