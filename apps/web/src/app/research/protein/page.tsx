'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type ProteinAnalysis, analyzeProtein } from '@/lib/research/proteinApi'
import { useState } from 'react'

export default function ProteinPage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<ProteinAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await analyzeProtein(gene))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <ResearchNav />
      <AnalysisLayout title="Protein Analysis" subtitle="UniProt + PDB + AlphaFold structures">
        <div className="mb-6 flex items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={gene} onChange={setGene} />
          <AnalyzeButton onClick={run} loading={loading} disabled={!gene} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="grid gap-4">
            <Card title={data.protein_name}>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-gray-500">Accession</dt>
                  <dd>{data.accession}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Organism</dt>
                  <dd>{data.organism}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Length</dt>
                  <dd>{data.length} aa</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Structures</dt>
                  <dd>{data.pdb_structures.length}</dd>
                </div>
              </dl>
            </Card>
            {data.function ? (
              <Card title="Function">
                <p className="text-sm text-gray-700">{data.function}</p>
              </Card>
            ) : null}
            {data.function_summary ? (
              <Card title="Function Summary">
                <p className="text-sm text-gray-700">{data.function_summary}</p>
              </Card>
            ) : null}
            {data.domains.length > 0 ? (
              <Card title="Domains">
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {data.domains.map((d) => (
                    <li key={d}>{d}</li>
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
