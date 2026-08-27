'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { KeyValue, KeyValueGrid } from '@/components/research/KeyValue'
import { ListBlock } from '@/components/research/ListBlock'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import { type VariantInterpretation, interpretVariant } from '@/lib/research/variantApi'
import { useState } from 'react'

export default function VariantPage() {
  const [gene, setGene] = useState('')
  const [variant, setVariant] = useState('')
  const [data, setData] = useState<VariantInterpretation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!gene) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      setData(await interpretVariant(gene, variant))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  function pathogenicityTone(p: string) {
    const low = p.toLowerCase()
    if (low.includes('pathogenic')) return 'red'
    if (low.includes('likely path')) return 'amber'
    if (low.includes('benign')) return 'green'
    if (low.includes('uncertain')) return 'amber'
    return 'default'
  }

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Variant Interpretation"
        icon="🧪"
        subtitle="Aggregate ClinVar, gnomAD frequency and Ensembl VEP, then generate an ACMG-informed pathogenicity assessment with Gemini."
      >
        <AnalysisForm
          fields={[
            {
              key: 'gene',
              label: 'Gene symbol',
              placeholder: 'e.g. BRCA1',
              value: gene,
              onChange: setGene,
            },
            {
              key: 'variant',
              label: 'Variant (HGVS)',
              placeholder: 'e.g. c.5074G>A',
              value: variant,
              onChange: setVariant,
              helper: 'Optional — leave blank to analyze top variant',
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!gene}
          submitLabel="Interpret variant"
        />
        <ErrorNotice error={error} />

        {loading ? (
          <div className="mt-6">
            <ResultSkeleton cards={2} />
          </div>
        ) : null}

        {data ? (
          <div className="mt-6 space-y-5">
            <Reveal>
              <Card
                icon="🧪"
                title={data.variant_description || `Variant — ${data.gene_symbol}`}
                subtitle={data.gene_symbol}
                action={
                  <Chip tone={pathogenicityTone(data.pathogenicity)}>
                    {data.pathogenicity || 'Not classified'}
                  </Chip>
                }
              >
                {data.data_sources.length > 0 ? (
                  <div className="mb-5 flex flex-wrap gap-1.5">
                    {data.data_sources.map((s) => (
                      <Chip key={s}>{s}</Chip>
                    ))}
                  </div>
                ) : null}
                <KeyValueGrid>
                  <KeyValue
                    label="Clinical actionability"
                    value={data.clinical_actionability || '—'}
                  />
                </KeyValueGrid>
              </Card>
            </Reveal>

            {data.clinvar ? (
              <Reveal delay={80}>
                <Card icon="🏥" title="ClinVar" subtitle={data.clinvar.condition}>
                  <div className="mb-4">
                    <Chip tone={pathogenicityTone(data.clinvar.clinical_significance)}>
                      {data.clinvar.clinical_significance || 'n/a'}
                    </Chip>
                  </div>
                  <KeyValueGrid>
                    <KeyValue label="ClinVar ID" value={data.clinvar.clinvar_id} />
                    <KeyValue label="Review status" value={data.clinvar.review_status} />
                    <KeyValue label="HGVS c." value={data.clinvar.hgvs_c} />
                    <KeyValue label="HGVS p." value={data.clinvar.hgvs_p} />
                  </KeyValueGrid>
                </Card>
              </Reveal>
            ) : null}

            {data.gnomad ? (
              <Reveal delay={120}>
                <Card
                  icon="🌍"
                  title="gnomAD Population Frequency"
                  subtitle={data.gnomad.variant_id}
                >
                  <KeyValueGrid>
                    <KeyValue
                      label="Allele frequency"
                      value={
                        data.gnomad.allele_frequency > 0
                          ? data.gnomad.allele_frequency.toExponential(3)
                          : '0'
                      }
                    />
                    <KeyValue label="Allele count" value={data.gnomad.allele_count} />
                    <KeyValue label="Allele number" value={data.gnomad.allele_number} />
                  </KeyValueGrid>
                </Card>
              </Reveal>
            ) : null}

            {data.vep ? (
              <Reveal delay={160}>
                <Card icon="🔍" title="Ensembl VEP Consequence">
                  <div className="mb-4 flex flex-wrap gap-1.5">
                    <Chip tone="amber">{data.vep.impact || 'Unknown impact'}</Chip>
                    <Chip>{data.vep.consequence}</Chip>
                  </div>
                  {data.vep.sift_prediction || data.vep.polyphen_prediction ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                      {data.vep.sift_prediction ? (
                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                            SIFT
                          </p>
                          <p className="mt-1 text-sm font-medium text-slate-800">
                            {data.vep.sift_prediction}
                            {data.vep.sift_score != null ? ` (${data.vep.sift_score})` : ''}
                          </p>
                        </div>
                      ) : null}
                      {data.vep.polyphen_prediction ? (
                        <div className="rounded-xl bg-slate-50 p-3">
                          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                            PolyPhen
                          </p>
                          <p className="mt-1 text-sm font-medium text-slate-800">
                            {data.vep.polyphen_prediction}
                            {data.vep.polyphen_score != null ? ` (${data.vep.polyphen_score})` : ''}
                          </p>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </Card>
              </Reveal>
            ) : null}

            {data.acmg_criteria.length > 0 ? (
              <Reveal delay={200}>
                <Card
                  icon="📋"
                  title="ACMG Criteria"
                  subtitle={`${data.acmg_criteria.length} criteria`}
                >
                  <ListBlock items={data.acmg_criteria} dense />
                </Card>
              </Reveal>
            ) : null}

            {data.reasoning ? (
              <Reveal delay={240}>
                <Card icon="🧠" title="Reasoning">
                  <p className="text-sm leading-relaxed text-slate-700">{data.reasoning}</p>
                </Card>
              </Reveal>
            ) : null}

            {data.summary ? (
              <Reveal delay={280}>
                <Card icon="✨" title="AI Summary">
                  <p className="text-sm leading-relaxed text-slate-700">{data.summary}</p>
                </Card>
              </Reveal>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
