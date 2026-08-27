'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import { type PathwayAnalysis, analyzePathway } from '@/lib/research/pathwayApi'
import { useState } from 'react'

export default function PathwayPage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<PathwayAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!gene) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      setData(await analyzePathway(gene))
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
        title="Pathway & Network Analysis"
        icon="🛣️"
        subtitle="Map a gene onto Reactome and KEGG pathways, reveal STRING protein interactions and functional enrichment."
      >
        <AnalysisForm
          fields={[
            {
              key: 'gene',
              label: 'Gene symbol',
              placeholder: 'e.g. BRCA1, TP53',
              value: gene,
              onChange: setGene,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!gene}
          submitLabel="Analyze pathways"
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

            <div className="grid gap-5 lg:grid-cols-2">
              <Reveal delay={80}>
                <Card
                  title="Reactome Pathways"
                  icon="🧬"
                  subtitle={`${data.reactome_pathways.length} pathways`}
                  action={<Chip tone="blue">Reactome</Chip>}
                >
                  {data.reactome_pathways.length === 0 ? (
                    <p className="text-sm text-slate-400">None found.</p>
                  ) : (
                    <ul className="space-y-2">
                      {data.reactome_pathways.slice(0, 15).map((p, i) => (
                        <li
                          key={`${p.st_id}-${i}`}
                          className="rounded-lg border border-slate-100 p-2.5 text-sm transition hover:border-genome-200 hover:bg-slate-50"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="text-slate-800">{p.name}</span>
                            {p.species ? <Chip>{p.species}</Chip> : null}
                          </div>
                          {p.st_id ? (
                            <p className="mt-0.5 font-mono text-xs text-genome-600">{p.st_id}</p>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </Reveal>

              <Reveal delay={140}>
                <Card
                  title="KEGG Pathways"
                  icon="🗺️"
                  subtitle={`${data.kegg_pathways.length} pathways`}
                  action={<Chip tone="red">KEGG</Chip>}
                >
                  {data.kegg_pathways.length === 0 ? (
                    <p className="text-sm text-slate-400">None found.</p>
                  ) : (
                    <ul className="space-y-2">
                      {data.kegg_pathways.slice(0, 15).map((p, i) => (
                        <li
                          key={`${p.pathway_id}-${i}`}
                          className="rounded-lg border border-slate-100 p-2.5 text-sm transition hover:border-genome-200 hover:bg-slate-50"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="text-slate-800">{p.name}</span>
                            {p.species ? <Chip>{p.species}</Chip> : null}
                          </div>
                          {p.pathway_id ? (
                            <p className="mt-0.5 font-mono text-xs text-genome-600">
                              {p.pathway_id}
                            </p>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </Reveal>
            </div>

            {data.string_interactions.length > 0 ? (
              <Reveal delay={200}>
                <Card
                  title="STRING Protein Interactions"
                  icon="🕸️"
                  subtitle={`${data.string_interactions.length} interactions`}
                  action={<Chip tone="green">STRING</Chip>}
                >
                  <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                    {data.string_interactions.slice(0, 24).map((ix, i) => (
                      <div
                        key={`${ix.from_gene}-${ix.to_gene}-${i}`}
                        className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3 py-2"
                      >
                        <span className="font-medium text-slate-800">{ix.from_gene}</span>
                        <svg
                          width="18"
                          height="18"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          className="text-genome-400"
                          aria-hidden="true"
                        >
                          <path d="M5 12h14M12 5v14" strokeLinecap="round" />
                        </svg>
                        <span className="font-medium text-slate-800">{ix.to_gene}</span>
                        <span className="ml-1 text-xs text-slate-400">
                          {(ix.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </Card>
              </Reveal>
            ) : null}

            {data.string_enrichment.length > 0 ? (
              <Reveal delay={260}>
                <Card
                  title="Functional Enrichment"
                  icon="📈"
                  subtitle={`${data.string_enrichment.length} terms`}
                  action={<Chip tone="green">STRING</Chip>}
                >
                  <ul className="space-y-2">
                    {data.string_enrichment.slice(0, 12).map((e, i) => (
                      <li
                        key={`${e.category}-${e.term}-${i}`}
                        className="flex items-start justify-between gap-2 rounded-lg border border-slate-100 p-2.5 text-sm"
                      >
                        <div className="min-w-0">
                          <span className="font-medium text-slate-800">{e.term}</span>
                          <span className="ml-2 text-xs text-slate-400">{e.description}</span>
                        </div>
                        <div className="flex shrink-0 items-center gap-1.5">
                          <Chip tone={e.fdr < 0.05 ? 'green' : 'amber'}>
                            {e.fdr > 0 ? `FDR ${e.fdr.toExponential(1)}` : '—'}
                          </Chip>
                        </div>
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
