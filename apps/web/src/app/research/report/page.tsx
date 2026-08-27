'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import { type DomainReport, type MultiDomainReport, generateReport } from '@/lib/research/reportApi'
import { useState } from 'react'

interface DomainSpec {
  title: string
  icon: string
  summary: string
  meta?: string
}

function domainSpec(data: MultiDomainReport, variant: string): DomainSpec[] {
  const g = data.gene_report as DomainReport & { data?: Record<string, unknown> }
  const v = data.variant_report
  const p = data.protein_report
  const l = data.literature_report as DomainReport & { paper_count?: number }
  const dr = data.drug_report as DomainReport & { drug_count?: number }
  const pw = data.pathway_report
  const ds = data.disease_report

  const oneOf = (r: DomainReport | undefined, key: string): string | undefined => {
    const val = r?.data?.[key]
    return val != null ? String(val) : undefined
  }

  const list = (r: DomainReport | undefined, key: string): number | undefined => {
    const val = r?.data?.[key]
    const n = Number(val)
    return Number.isFinite(n) && n > 0 ? n : undefined
  }

  return [
    {
      title: 'Gene',
      icon: '🧬',
      summary: g?.summary || '',
      meta: oneOf(g, 'gene'),
    },
    {
      title: 'Variant',
      icon: '🧪',
      summary: v?.summary || '',
      meta: oneOf(v, 'variant') || variant || 'Top variant',
    },
    {
      title: 'Protein',
      icon: '🔬',
      summary: p?.summary || '',
      meta: oneOf(p, 'uniprot_id') || 'UniProt',
    },
    {
      title: 'Literature',
      icon: '📚',
      summary: l?.summary || '',
      meta: l?.paper_count ? `${l.paper_count} papers` : '0 papers',
    },
    {
      title: 'Drug',
      icon: '💊',
      summary: dr?.summary || '',
      meta: dr?.drug_count ? `${dr.drug_count} compounds` : '0 compounds',
    },
    {
      title: 'Pathway',
      icon: '🛣️',
      summary: pw?.summary || '',
      meta: list(pw, 'reactome')
        ? `${list(pw, 'reactome')} Reactome · ${list(pw, 'kegg') ?? 0} KEGG`
        : 'No pathways',
    },
    {
      title: 'Disease',
      icon: '🩺',
      summary: ds?.summary || '',
      meta: list(ds, 'diseases') ? `${list(ds, 'diseases')} diseases` : 'No diseases',
    },
  ]
}

export default function ReportPage() {
  const [gene, setGene] = useState('')
  const [variant, setVariant] = useState('')
  const [data, setData] = useState<MultiDomainReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!gene) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      setData(await generateReport(gene, variant))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const specs = data ? domainSpec(data, variant) : []

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Multi-Domain Report"
        icon="📊"
        subtitle="One unified executive summary across all seven analytic domains, powered by Gemini."
      >
        <AnalysisForm
          fields={[
            {
              key: 'gene',
              label: 'Gene symbol',
              placeholder: 'e.g. BRCA1',
              value: gene,
              onChange: setGene,
            },
            {
              key: 'variant',
              label: 'Variant (optional)',
              placeholder: 'e.g. c.5074G>A',
              value: variant,
              onChange: setVariant,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!gene}
          submitLabel="Generate report"
        />
        <ErrorNotice error={error} />

        {loading ? (
          <div className="mt-6">
            <ResultSkeleton cards={3} />
          </div>
        ) : null}

        {data ? (
          <div className="mt-6 space-y-6">
            <Reveal>
              <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-genome-700 via-genome-600 to-indigo-600 p-8 text-white shadow-glow-lg">
                <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/10 blur-3xl" />
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-genome-200">
                      Executive Summary
                    </p>
                    <h2 className="mt-1 text-3xl font-extrabold tracking-tight">{gene}</h2>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {data.sources.map((s) => (
                      <span
                        key={s}
                        className="rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white backdrop-blur"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="mt-5 whitespace-pre-wrap text-sm leading-relaxed text-genome-50 sm:text-base">
                  {data.executive_summary || 'Generating summary…'}
                </p>
              </section>
            </Reveal>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {specs.map((s, i) => (
                <Reveal key={s.title} delay={i * 60}>
                  <Card icon={s.icon} title={s.title} subtitle={s.meta} className="h-full">
                    {s.summary ? (
                      <p className="line-clamp-5 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                        {s.summary}
                      </p>
                    ) : (
                      <p className="text-sm text-slate-400">No data available for this domain.</p>
                    )}
                    <div className="mt-3 flex items-center justify-between">
                      <Chip
                        tone={
                          s.meta &&
                          !s.meta.includes('No') &&
                          s.meta !== '0 papers' &&
                          s.meta !== '0 compounds'
                            ? 'blue'
                            : 'default'
                        }
                      >
                        {s.summary ? 'Analyzed' : 'Unavailable'}
                      </Chip>
                    </div>
                  </Card>
                </Reveal>
              ))}
            </div>
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
