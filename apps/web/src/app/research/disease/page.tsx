'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import { type DiseaseAnalysis, searchDiseases } from '@/lib/research/diseaseApi'
import { useState } from 'react'

export default function DiseasePage() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<DiseaseAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!query) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      setData(await searchDiseases(query))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Disease Search"
        icon="🩺"
        subtitle="Discover diseases and gene–disease associations from OpenTargets, Disease Ontology and Monarch."
      >
        <AnalysisForm
          fields={[
            {
              key: 'query',
              label: 'Disease name',
              placeholder: 'e.g. breast cancer, Alzheimer',
              value: query,
              onChange: setQuery,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!query}
          submitLabel="Search diseases"
        />
        <ErrorNotice error={error} />

        {loading ? (
          <div className="mt-6">
            <ResultSkeleton cards={2} />
          </div>
        ) : null}

        {data ? (
          <div className="mt-6 space-y-5">
            {data.ai_analysis ? (
              <Reveal>
                <Card icon="✨" title="AI Synthesis">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                    {data.ai_analysis}
                  </p>
                </Card>
              </Reveal>
            ) : null}

            {data.diseases.length > 0 ? (
              <Reveal delay={80}>
                <Card
                  title="Diseases"
                  icon="🩺"
                  subtitle={`${data.diseases.length} results`}
                  action={<Chip tone="blue">Disease Ontology</Chip>}
                >
                  <ul className="space-y-2.5">
                    {data.diseases.slice(0, 12).map((d, i) => (
                      <li
                        key={`${d.disease_id}-${i}`}
                        className="animate-fade-in-up rounded-xl border border-slate-100 p-3.5 transition hover:border-genome-200 hover:bg-slate-50"
                        style={{ animationDelay: `${Math.min(i * 60, 360)}ms` }}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-medium text-slate-900">{d.name}</span>
                          <span className="font-mono text-xs text-genome-600">{d.disease_id}</span>
                        </div>
                        {d.description ? (
                          <p className="mt-1 line-clamp-2 text-sm text-slate-500">
                            {d.description}
                          </p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </Card>
              </Reveal>
            ) : null}

            {data.gene_disease_associations.length > 0 ? (
              <Reveal delay={140}>
                <Card
                  title="Gene–Disease Associations"
                  icon="🧬"
                  subtitle={`${data.gene_disease_associations.length} associations`}
                  action={<Chip tone="green">OpenTargets</Chip>}
                >
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    {data.gene_disease_associations.slice(0, 12).map((a, i) => (
                      <div
                        key={`${a.gene_id}-${a.disease_id}-${i}`}
                        className="rounded-xl border border-slate-100 bg-slate-50 p-3"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{a.gene_symbol}</span>
                          <Chip tone={a.score > 0.5 ? 'green' : 'default'}>
                            {(a.score * 100).toFixed(0)}%
                          </Chip>
                        </div>
                        <p className="mt-1 text-sm text-slate-600">{a.disease_name}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </Reveal>
            ) : null}

            {data.monarch_results.length > 0 ? (
              <Reveal delay={200}>
                <Card
                  title="Monarch Associations"
                  icon="🏛️"
                  subtitle={`${data.monarch_results.length} results`}
                  action={<Chip>Monarch</Chip>}
                >
                  <ul className="space-y-2">
                    {data.monarch_results.slice(0, 12).map((m, i) => (
                      <li
                        key={`${m.disease_id}-${i}`}
                        className="flex items-start justify-between gap-2 rounded-lg border border-slate-100 p-2.5 text-sm"
                      >
                        <span className="text-slate-800">{m.disease_name}</span>
                        <span className="font-mono text-xs text-genome-600">{m.disease_id}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </Reveal>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
