interface AnalysisLayoutProps {
  title: string
  subtitle?: string
  children: React.ReactNode
}

export function AnalysisLayout({ title, subtitle, children }: AnalysisLayoutProps) {
  return (
    <main className="mx-auto max-w-7xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">{title}</h1>
        {subtitle ? <p className="mt-1 text-sm text-gray-600">{subtitle}</p> : null}
      </header>
      {children}
    </main>
  )
}
