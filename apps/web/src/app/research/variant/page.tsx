'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type VariantInterpretation, interpretVariant } from '@/lib/research/variantApi'
import { useState } from 'react'

export default function VariantPage() {
  const [gene, setGene] = useState('')
  const [variant, setVariant] = useState('')
  const [data, setData] = useState<VariantInterpretation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await interpretVariant(gene, variant))
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
        title="Variant Interpretation"
        subtitle="ClinVar + gnomAD + Ensembl VEP + Gemini pathogenicity analysis"
      >
        <div className="mb-6 flex flex-wrap items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={gene} onChange={setGene} />
          <Input
            label="Variant (HGVS)"
            placeholder="e.g. c.5074G>A"
            value={variant}
            onChange={setVariant}
          />
          <AnalyzeButton onClick={run} loading={loading} disabled={!gene || !variant} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="grid gap-4">
            <Card title={`${data.variant_description} (${data.gene_symbol})`}>
              <dl className="grid gap-2 text-sm">
                <div>
                  <dt className="text-gray-500">Pathogenicity</dt>
                  <dd className="font-medium">{data.pathogenicity}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Clinical Actionability</dt>
                  <dd>{data.clinical_actionability}</dd>
                </div>
              </dl>
            </Card>
            {data.acmg_criteria.length > 0 ? (
              <Card title="ACMG Criteria">
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {data.acmg_criteria.map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              </Card>
            ) : null}
            {data.clinvar ? (
              <Card title="ClinVar">
                <dl className="grid gap-1 text-sm">
                  <div>
                    <dt className="text-gray-500">ID</dt>
                    <dd>{data.clinvar.clinvar_id}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Significance</dt>
                    <dd>{data.clinvar.clinical_significance}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Condition</dt>
                    <dd>{data.clinvar.condition}</dd>
                  </div>
                </dl>
              </Card>
            ) : null}
            {data.gnomad ? (
              <Card title="gnomAD">
                <dl className="grid gap-1 text-sm">
                  <div>
                    <dt className="text-gray-500">Variant ID</dt>
                    <dd>{data.gnomad.variant_id}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Allele Frequency</dt>
                    <dd>{data.gnomad.allele_frequency.toExponential(3)}</dd>
                  </div>
                </dl>
              </Card>
            ) : null}
            {data.vep ? (
              <Card title="VEP Consequence">
                <dl className="grid gap-1 text-sm">
                  <div>
                    <dt className="text-gray-500">Consequence</dt>
                    <dd>{data.vep.consequence}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Impact</dt>
                    <dd>{data.vep.impact}</dd>
                  </div>
                </dl>
              </Card>
            ) : null}
            {data.reasoning ? (
              <Card title="Reasoning">
                <p className="text-sm text-gray-700">{data.reasoning}</p>
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
