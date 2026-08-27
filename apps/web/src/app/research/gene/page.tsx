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
import { type GeneAnalysis, analyzeGene } from '@/lib/research/geneApi'
import { useState } from 'react'

export default function GenePage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<GeneAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!gene) return
    setLoading(true)
    setError(null)
    setData(null)
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
        icon="🧬"
        subtitle="Query NCBI for real gene annotations and combine with Gemini for function, variants, diseases, drug targets and clinical significance."
      >
        <AnalysisForm
          fields={[
            {
              key: 'gene',
              label: 'Gene symbol',
              placeholder: 'e.g. BRCA1, TP53',
              value: gene,
              onChange: setGene,
              helper: 'Enter a valid HGNC gene symbol',
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!gene}
          submitLabel="Analyze gene"
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
                icon="🧬"
                title={data.name || data.gene_symbol}
                subtitle={`Gene ${data.gene_id}`}
                action={<Chip tone="blue">{data.gene_type || 'gene'}</Chip>}
              >
                <div className="flex flex-wrap items-center gap-2">
                  {data.aliases.length > 0 ? (
                    data.aliases.slice(0, 8).map((a) => <Chip key={a}>{a}</Chip>)
                  ) : (
                    <Chip>{data.gene_symbol}</Chip>
                  )}
                </div>
                <div className="mt-5">
                  <KeyValueGrid>
                    <KeyValue label="Gene ID" value={data.gene_id} />
                    <KeyValue label="Chromosome" value={data.chromosome} />
                    <KeyValue label="Map location" value={data.map_location} />
                    <KeyValue label="Organism" value={data.organism} />
                    <KeyValue label="Source" value={data.source} />
                  </KeyValueGrid>
                </div>
              </Card>
            </Reveal>

            {data.description ? (
              <Reveal delay={80}>
                <Card icon="📄" title="Description">
                  <p className="text-sm leading-relaxed text-slate-700">{data.description}</p>
                </Card>
              </Reveal>
            ) : null}

            {data.function ? (
              <Reveal delay={120}>
                <Card icon="⚙️" title="Function">
                  <p className="text-sm leading-relaxed text-slate-700">{data.function}</p>
                </Card>
              </Reveal>
            ) : null}

            {data.associated_diseases.length > 0 ? (
              <Reveal delay={160}>
                <Card
                  icon="🩺"
                  title="Associated Diseases"
                  subtitle={`${data.associated_diseases.length} conditions`}
                >
                  <ListBlock items={data.associated_diseases} />
                </Card>
              </Reveal>
            ) : null}

            {data.key_variants.length > 0 ? (
              <Reveal delay={200}>
                <Card
                  icon="🧪"
                  title="Key Variants"
                  subtitle={`${data.key_variants.length} notable variants`}
                >
                  <ListBlock items={data.key_variants} />
                </Card>
              </Reveal>
            ) : null}

            {data.drug_targets.length > 0 ? (
              <Reveal delay={240}>
                <Card icon="💊" title="Drug Targets">
                  <ListBlock items={data.drug_targets} />
                </Card>
              </Reveal>
            ) : null}

            {data.clinical_significance ? (
              <Reveal delay={280}>
                <Card icon="🏥" title="Clinical Significance">
                  <p className="text-sm leading-relaxed text-slate-700">
                    {data.clinical_significance}
                  </p>
                </Card>
              </Reveal>
            ) : null}

            {data.summary ? (
              <Reveal delay={320}>
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
