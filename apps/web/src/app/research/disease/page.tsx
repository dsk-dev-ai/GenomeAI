'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type DiseaseAnalysis, searchDiseases } from '@/lib/research/diseaseApi'
import { useState } from 'react'

export default function DiseasePage() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<DiseaseAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
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
      <AnalysisLayout title="Disease Search" subtitle="OpenTargets + Disease Ontology + Monarch">
        <div className="mb-6 flex items-end gap-3">
          <Input
            label="Disease name"
            placeholder="e.g. breast cancer"
            value={query}
            onChange={setQuery}
          />
          <AnalyzeButton onClick={run} loading={loading} disabled={!query} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="grid gap-4">
            <Card title="AI Analysis">
              <p className="text-sm text-gray-700">{data.ai_analysis}</p>
            </Card>
            {data.diseases.length > 0 ? (
              <Card title="Diseases">
                <ul className="space-y-2">
                  {data.diseases.map((d) => (
                    <li key={`${d.disease_id}-${d.name}`} className="text-sm">
                      <span className="font-medium text-gray-900">{d.name}</span>
                      <span className="ml-2 text-xs text-gray-500">{d.disease_id}</span>
                      {d.description ? (
                        <p className="mt-0.5 text-xs text-gray-600">
                          {d.description.slice(0, 150)}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.monarch_results.length > 0 ? (
              <Card title="Monarch Associations">
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {data.monarch_results.map((m) => (
                    <li key={`${m.disease_id}-${m.disease_name}`}>
                      {m.disease_name} ({m.disease_id})
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
