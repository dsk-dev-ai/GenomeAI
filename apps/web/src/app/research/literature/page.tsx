'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import {
  type LiteratureSearch,
  analyzeLiterature,
  searchLiterature,
} from '@/lib/research/literatureApi'
import { useState } from 'react'

export default function LiteraturePage() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<LiteratureSearch | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
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

  const papers = search
    ? search.europepmc_articles.map((a) => ({
        id: String(a.pmid ?? a.pmcid ?? ''),
        title: String(a.title ?? 'Untitled'),
        source: 'Europe PMC',
        year: a.pub_date != null ? String(a.pub_date) : 'n/a',
        abstract: a.abstract != null ? String(a.abstract) : null,
      }))
    : []
  const ssPapers = search
    ? search.semanticscholar_papers.map((p) => ({
        id: String(p.paperId ?? p.id ?? ''),
        title: String(p.title ?? 'Untitled'),
        source: 'Semantic Scholar',
        year: p.year != null ? String(p.year) : 'n/a',
        abstract: p.abstract != null ? String(p.abstract) : null,
      }))
    : []

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Literature Search"
        subtitle="Europe PMC + Semantic Scholar research papers"
      >
        <div className="mb-6 flex items-end gap-3">
          <Input
            label="Query"
            placeholder="e.g. BRCA1 breast cancer"
            value={query}
            onChange={setQuery}
          />
          <AnalyzeButton onClick={run} loading={loading} disabled={!query} />
        </div>
        <ErrorNotice error={error} />
        {search ? (
          <div className="grid gap-4">
            {aiAnalysis ? (
              <Card title="AI Analysis">
                <p className="text-sm text-gray-700">{aiAnalysis}</p>
              </Card>
            ) : null}
            {papers.length > 0 ? (
              <Card title={`Europe PMC (${papers.length})`}>
                <ul className="space-y-3">
                  {papers.map((p) => (
                    <li key={p.id} className="border-b border-gray-100 pb-2 last:border-0">
                      <p className="text-sm font-medium text-gray-900">{p.title}</p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {p.source} · {p.year}
                      </p>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {ssPapers.length > 0 ? (
              <Card title={`Semantic Scholar (${ssPapers.length})`}>
                <ul className="space-y-3">
                  {ssPapers.map((p) => (
                    <li key={p.id} className="border-b border-gray-100 pb-2 last:border-0">
                      <p className="text-sm font-medium text-gray-900">{p.title}</p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {p.source} · {p.year}
                      </p>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
