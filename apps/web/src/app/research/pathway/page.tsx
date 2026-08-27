'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type PathwayAnalysis, analyzePathway } from '@/lib/research/pathwayApi'
import { useState } from 'react'

export default function PathwayPage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<PathwayAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
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
        title="Pathway Analysis"
        subtitle="Reactome + STRING + KEGG biological pathways"
      >
        <div className="mb-6 flex items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={gene} onChange={setGene} />
          <AnalyzeButton onClick={run} loading={loading} disabled={!gene} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="grid gap-4">
            <Card title="AI Analysis">
              <p className="text-sm text-gray-700">{data.ai_analysis}</p>
            </Card>
            {data.reactome_pathways.length > 0 ? (
              <Card title="Reactome Pathways">
                <ul className="space-y-2">
                  {data.reactome_pathways.map((p) => (
                    <li key={`${p.st_id}-${p.name}`} className="text-sm">
                      <span className="text-gray-900">{p.name}</span>
                      <span className="ml-2 text-xs text-gray-500">{p.st_id}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.kegg_pathways.length > 0 ? (
              <Card title="KEGG Pathways">
                <ul className="space-y-2">
                  {data.kegg_pathways.map((p) => (
                    <li key={`${p.pathway_id}-${p.name}`} className="text-sm">
                      <span className="text-gray-900">{p.name}</span>
                      <span className="ml-2 text-xs text-gray-500">{p.pathway_id}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.string_interactions.length > 0 ? (
              <Card title="STRING Interactions">
                <ul className="space-y-1 text-sm">
                  {data.string_interactions.map((ix, i) => (
                    <li key={`${ix.from_gene}-${ix.to_gene}-${i}`}>
                      {ix.from_gene} ↔ {ix.to_gene}{' '}
                      <span className="text-xs text-gray-500">score {ix.score.toFixed(3)}</span>
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
