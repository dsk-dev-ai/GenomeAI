'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type DrugSearch, searchDrugs } from '@/lib/research/drugApi'
import { useState } from 'react'

export default function DrugPage() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<DrugSearch | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setSearch(await searchDrugs(query))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <ResearchNav />
      <AnalysisLayout title="Drug Search" subtitle="ChEMBL + PubChem compounds targeting a gene">
        <div className="mb-6 flex items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={query} onChange={setQuery} />
          <AnalyzeButton onClick={run} loading={loading} disabled={!query} />
        </div>
        <ErrorNotice error={error} />
        {search ? (
          <div className="grid gap-4">
            {search.chembl_drugs.length > 0 ? (
              <Card title={`ChEMBL Compounds (${search.chembl_drugs.length})`}>
                <ul className="space-y-2">
                  {search.chembl_drugs.map((d, i) => (
                    <li
                      key={String(d.id ?? i)}
                      className="border-b border-gray-100 pb-2 last:border-0 text-sm"
                    >
                      <span className="font-medium text-gray-900">
                        {String(d.name ?? d.pref_name ?? 'Unknown')}
                      </span>
                      <span className="ml-2 text-xs text-gray-500">
                        {String(d.id ?? d.chembl_id ?? '')}
                      </span>
                      {d.molecular_weight != null ? (
                        <span className="ml-2 text-xs text-gray-500">
                          MW {Number(d.molecular_weight).toFixed(2)}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </Card>
            ) : (
              <Card title="ChEMBL Compounds">
                <p className="text-sm text-gray-400">No compounds found</p>
              </Card>
            )}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
