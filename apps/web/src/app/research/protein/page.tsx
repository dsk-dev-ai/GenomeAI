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
import { type PDBInfo, type ProteinAnalysis, analyzeProtein } from '@/lib/research/proteinApi'
import { useState } from 'react'

export default function ProteinPage() {
  const [gene, setGene] = useState('')
  const [data, setData] = useState<ProteinAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!gene) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      setData(await analyzeProtein(gene))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const pdb = (data?.pdb_structures ?? []) as PDBInfo[]

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Protein Analysis"
        icon="🔬"
        subtitle="Combine UniProt function, PDB experimental structures and AlphaFold predictions into a protein-centric analysis."
      >
        <AnalysisForm
          fields={[
            {
              key: 'gene',
              label: 'Gene symbol',
              placeholder: 'e.g. BRCA1, TP53',
              value: gene,
              onChange: setGene,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!gene}
          submitLabel="Analyze protein"
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
                icon="🔬"
                title={data.protein_name || data.accession || gene}
                subtitle={data.accession}
                action={
                  <Chip tone="green">
                    {data.length > 0 ? `${data.length} aa` : 'Unknown length'}
                  </Chip>
                }
              >
                <div className="flex flex-wrap gap-1.5">
                  {data.organism ? <Chip>{data.organism}</Chip> : null}
                  {data.gene_names.map((n) => (
                    <Chip key={n}>{n}</Chip>
                  ))}
                  {data.data_sources.map((s) => (
                    <Chip key={s} tone="blue">
                      {s}
                    </Chip>
                  ))}
                </div>
                <div className="mt-5">
                  <KeyValueGrid>
                    <KeyValue label="Accession" value={data.accession} />
                    <KeyValue label="Length" value={data.length > 0 ? `${data.length} aa` : '—'} />
                    <KeyValue label="Subcellular location" value={data.subcellular_location} />
                    <KeyValue label="PDB structures" value={pdb.length} />
                    <KeyValue label="Clinical significance" value={data.clinical_significance} />
                  </KeyValueGrid>
                </div>
              </Card>
            </Reveal>

            {data.function ? (
              <Reveal delay={80}>
                <Card icon="⚙️" title="Function">
                  <p className="text-sm leading-relaxed text-slate-700">{data.function}</p>
                </Card>
              </Reveal>
            ) : null}
            {data.function_summary ? (
              <Reveal delay={120}>
                <Card icon="✨" title="Function Summary">
                  <p className="text-sm leading-relaxed text-slate-700">{data.function_summary}</p>
                </Card>
              </Reveal>
            ) : null}

            {data.domains.length > 0 ? (
              <Reveal delay={160}>
                <Card icon="🧩" title="Domains" subtitle={`${data.domains.length} domains`}>
                  <ListBlock items={data.domains} dense />
                </Card>
              </Reveal>
            ) : null}

            {pdb.length > 0 ? (
              <Reveal delay={200}>
                <Card
                  icon="🧊"
                  title="Experimental Structures (PDB)"
                  subtitle={`${pdb.length} structures`}
                >
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {pdb.map((s) => (
                      <div
                        key={s.pdb_id}
                        className="rounded-xl border border-slate-100 bg-slate-50 p-3 transition hover:border-genome-200"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-sm font-bold text-genome-700">
                            {s.pdb_id}
                          </span>
                          <Chip>{s.method || '—'}</Chip>
                        </div>
                        <p className="mt-1.5 line-clamp-2 text-xs text-slate-500">
                          {s.title || 'No title'}
                        </p>
                        {s.resolution > 0 ? (
                          <p className="mt-1 text-xs text-slate-400">
                            Resolution: {s.resolution.toFixed(2)} Å
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </Card>
              </Reveal>
            ) : null}

            {data.alphafold ? (
              <Reveal delay={240}>
                <Card icon="🤖" title="AlphaFold Prediction" subtitle={data.alphafold.alphafold_id}>
                  <KeyValueGrid>
                    <KeyValue label="Length" value={data.alphafold.sequence_length} />
                    <KeyValue
                      label="Confidence version"
                      value={data.alphafold.confidence_version}
                    />
                  </KeyValueGrid>
                </Card>
              </Reveal>
            ) : null}

            {data.disease_associations.length > 0 ? (
              <Reveal delay={280}>
                <Card icon="🩺" title="Disease Associations">
                  <ListBlock items={data.disease_associations} dense />
                </Card>
              </Reveal>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
