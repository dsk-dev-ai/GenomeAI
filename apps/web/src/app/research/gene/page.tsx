'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type GeneAnalysis, analyzeGene } from '@/lib/research/geneApi'
import { useState } from 'react'

export default function GenePage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<GeneAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await analyzeGene(gene))
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
        title="Gene Analysis"
        subtitle="Query NCBI + Gemini for comprehensive gene annotations"
      >
        <div className="mb-6 flex items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={gene} onChange={setGene} />
          <AnalyzeButton onClick={run} loading={loading} disabled={!gene} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="grid gap-4">
            <Card title={data.name}>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-gray-500">Gene Symbol</dt>
                  <dd>{data.gene_symbol}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Gene ID</dt>
                  <dd>{data.gene_id}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Organism</dt>
                  <dd>{data.organism}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Chromosome</dt>
                  <dd>{data.chromosome}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Location</dt>
                  <dd>{data.map_location}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Type</dt>
                  <dd>{data.gene_type}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Source</dt>
                  <dd>{data.source}</dd>
                </div>
              </dl>
            </Card>
            {data.description ? (
              <Card title="Description">
                <p className="text-sm text-gray-700">{data.description}</p>
              </Card>
            ) : null}
            {data.function ? (
              <Card title="Function">
                <p className="text-sm text-gray-700">{data.function}</p>
              </Card>
            ) : null}
            {data.associated_diseases.length > 0 ? (
              <Card title="Associated Diseases">
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {data.associated_diseases.map((d) => (
                    <li key={d}>{d}</li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.key_variants.length > 0 ? (
              <Card title="Key Variants">
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {data.key_variants.map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.summary ? (
              <Card title="Summary">
                <p className="text-sm text-gray-700">{data.summary}</p>
              </Card>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
