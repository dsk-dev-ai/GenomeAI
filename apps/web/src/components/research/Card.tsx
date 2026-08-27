interface CardProps {
  title?: string
  icon?: string
  subtitle?: string
  children: React.ReactNode
  action?: React.ReactNode
  className?: string
  delay?: number
}

export function Card({
  title,
  icon,
  subtitle,
  action,
  children,
  className = '',
  delay = 0,
}: CardProps) {
  return (
    <section
      className={`group animate-fade-in-up rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:border-genome-200 hover:shadow-card-hover ${className}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      {title ? (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5">
            {icon ? (
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-genome-50 text-base">
                {icon}
              </span>
            ) : null}
            <div>
              <h2 className="font-semibold text-slate-900">{title}</h2>
              {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
            </div>
          </div>
          {action ? <div className="shrink-0">{action}</div> : null}
        </header>
      ) : null}
      {children}
    </section>
  )
}
