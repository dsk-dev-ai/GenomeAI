'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import {
  type LiteratureSearch,
  analyzeLiterature,
  searchLiterature,
} from '@/lib/research/literatureApi'
import { useState } from 'react'

interface Paper {
  id: string
  title: string
  source: string
  year: string
  journal?: string
  authors?: string
}

export default function LiteraturePage() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<LiteratureSearch | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!query) return
    setLoading(true)
    setError(null)
    setSearch(null)
    try {
      const searchResult = await searchLiterature(query, 10)
      setSearch(searchResult)
      const analysis = await analyzeLiterature(query, 5)
      setAiAnalysis(typeof analysis.ai_analysis === 'string' ? analysis.ai_analysis : '')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const papers: Paper[] = search
    ? search.europepmc_articles.map((a) => ({
        id: String(a.pmid ?? a.pmcid ?? ''),
        title: String(a.title ?? 'Untitled'),
        source: 'Europe PMC',
        year: a.pub_date != null ? String(a.pub_date) : 'n/a',
        journal: a.journal != null ? String(a.journal) : undefined,
        authors:
          Array.isArray(a.authors) && a.authors.length > 0
            ? String(
                (a.authors as Array<Record<string, unknown>>)
                  .map((x) => x.fullName ?? x.lastName ?? '')
                  .filter(Boolean)
                  .slice(0, 4)
                  .join(', '),
              )
            : undefined,
      }))
    : []
  const ssPapers: Paper[] = search
    ? search.semanticscholar_papers.map((p) => ({
        id: String(p.paperId ?? p.id ?? ''),
        title: String(p.title ?? 'Untitled'),
        source: 'Semantic Scholar',
        year: p.year != null ? String(p.year) : 'n/a',
      }))
    : []

  const all = [...papers, ...ssPapers]

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Literature Search"
        icon="📚"
        subtitle="Discover the latest biomedical research from Europe PMC and Semantic Scholar, synthesized by Gemini."
      >
        <AnalysisForm
          fields={[
            {
              key: 'query',
              label: 'Search query',
              placeholder: 'e.g. BRCA1 breast cancer treatment',
              value: query,
              onChange: setQuery,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!query}
          submitLabel="Search literature"
        />
        <ErrorNotice error={error} />

        {loading ? (
          <div className="mt-6">
            <ResultSkeleton cards={2} />
          </div>
        ) : null}

        {search ? (
          <div className="mt-6 space-y-5">
            {aiAnalysis ? (
              <Reveal>
                <Card icon="✨" title="AI Synthesis">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                    {aiAnalysis}
                  </p>
                </Card>
              </Reveal>
            ) : null}

            <Reveal delay={80}>
              <Card
                title={`Results (${all.length} papers)`}
                icon="📑"
                action={
                  <div className="flex gap-1.5">
                    <Chip tone="blue">{search.europepmc_count} EPMC</Chip>
                    <Chip>{search.semanticscholar_count} S2</Chip>
                  </div>
                }
              >
                {all.length === 0 ? (
                  <p className="text-sm text-slate-400">No papers found.</p>
                ) : (
                  <ul className="space-y-3">
                    {all.map((p, i) => (
                      <li
                        key={`${p.source}-${p.id}-${i}`}
                        className="animate-fade-in-up rounded-xl border border-slate-100 p-4 transition hover:border-genome-200 hover:bg-slate-50"
                        style={{ animationDelay: `${Math.min(i * 60, 480)}ms` }}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <p className="font-medium leading-snug text-slate-900">{p.title}</p>
                          <Chip tone={p.source === 'Europe PMC' ? 'blue' : 'default'}>
                            {p.source}
                          </Chip>
                        </div>
                        <p className="mt-1.5 text-xs text-slate-500">
                          {p.journal ? <span>{p.journal} · </span> : null}
                          {p.year}
                        </p>
                        {p.authors ? (
                          <p className="mt-1 text-xs text-slate-400">{p.authors}</p>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </Reveal>
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
