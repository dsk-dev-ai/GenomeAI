'use client'

import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { AnalyzeButton } from '@/components/research/AnalyzeButton'
import { Card } from '@/components/research/Card'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { Input } from '@/components/research/Input'
import { ResearchNav } from '@/components/research/ResearchNav'
import { type DomainReport, type MultiDomainReport, generateReport } from '@/lib/research/reportApi'
import { useState } from 'react'

function DomainSection({
  title,
  report,
  meta,
}: {
  title: string
  report: DomainReport | undefined
  meta?: string
}) {
  const summary = report?.summary
  if (!summary && !meta) return null
  return (
    <Card title={title}>
      {meta ? <p className="mb-1 text-xs font-medium text-gray-500">{meta}</p> : null}
      {summary ? (
        <p className="whitespace-pre-wrap text-sm text-gray-700">{summary ?? ''}</p>
      ) : (
        <p className="text-sm text-gray-400">No data available</p>
      )}
    </Card>
  )
}

export default function ReportPage() {
  const [gene, setGene] = useState('')
  const [variant, setVariant] = useState('')
  const [data, setData] = useState<MultiDomainReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setError(null)
    try {
      setData(await generateReport(gene, variant))
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
        title="Multi-Domain Report"
        subtitle="Aggregates all 7 domains into one executive summary"
      >
        <div className="mb-6 flex flex-wrap items-end gap-3">
          <Input label="Gene symbol" placeholder="e.g. BRCA1" value={gene} onChange={setGene} />
          <Input
            label="Variant (optional)"
            placeholder="e.g. c.5074G>A"
            value={variant}
            onChange={setVariant}
          />
          <AnalyzeButton onClick={run} loading={loading} disabled={!gene} />
        </div>
        <ErrorNotice error={error} />
        {data ? (
          <div className="space-y-6">
            <section className="rounded-lg border border-blue-200 bg-blue-50 p-6">
              <h2 className="mb-3 text-lg font-bold text-gray-900">
                Executive Summary — {data.gene}
              </h2>
              <div className="mb-3 flex flex-wrap gap-2">
                {data.sources.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700"
                  >
                    {s}
                  </span>
                ))}
              </div>
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
                {data.executive_summary || 'Generating summary…'}
              </pre>
            </section>
            <div className="grid gap-4 lg:grid-cols-2">
              <DomainSection
                title="Gene"
                report={data.gene_report}
                meta={String(data.gene_report?.data?.gene ?? '')}
              />
              <DomainSection
                title="Variant"
                report={data.variant_report}
                meta={String(data.variant_report?.data?.variant ?? variant)}
              />
              <DomainSection
                title="Protein"
                report={data.protein_report}
                meta={String(data.protein_report?.data?.uniprot_id ?? '')}
              />
              <DomainSection
                title="Literature"
                report={data.literature_report}
                meta={
                  data.literature_report?.paper_count
                    ? `${data.literature_report.paper_count} papers`
                    : undefined
                }
              />
              <DomainSection
                title="Drug"
                report={data.drug_report}
                meta={
                  data.drug_report?.drug_count ? `${data.drug_report.drug_count} drugs` : undefined
                }
              />
              <DomainSection
                title="Pathway"
                report={data.pathway_report}
                meta={
                  String(data.pathway_report?.data?.reactome ?? '')
                    ? 'Reactome + KEGG + STRING'
                    : undefined
                }
              />
              <DomainSection
                title="Disease"
                report={data.disease_report}
                meta={
                  String(data.disease_report?.data?.diseases ?? '')
                    ? 'OpenTargets + DO + Monarch'
                    : undefined
                }
              />
            </div>
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
