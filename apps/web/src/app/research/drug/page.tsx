'use client'

import { AnalysisForm } from '@/components/research/AnalysisForm'
import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { Card } from '@/components/research/Card'
import { Chip } from '@/components/research/Chip'
import { ErrorNotice } from '@/components/research/ErrorNotice'
import { ResearchNav } from '@/components/research/ResearchNav'
import { Reveal } from '@/components/research/Reveal'
import { ResultSkeleton } from '@/components/research/Skeleton'
import { type DrugSearch, searchDrugs } from '@/lib/research/drugApi'
import { useState } from 'react'

interface Drug {
  id: string
  name: string
  mw?: number
  maxPhase?: number
  smiles?: string
  type?: string
}

export default function DrugPage() {
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState<DrugSearch | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    if (!query) return
    setLoading(true)
    setError(null)
    setSearch(null)
    try {
      setSearch(await searchDrugs(query))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const drugs: Drug[] = (search?.chembl_drugs ?? []).map((d) => ({
    id: String(d.id ?? d.molecule_chembl_id ?? ''),
    name: String(d.name ?? d.pref_name ?? 'Unknown'),
    mw: d.molecular_weight != null ? Number(d.molecular_weight) : undefined,
    maxPhase:
      d.max_phase != null && !Number.isNaN(Number(d.max_phase)) ? Number(d.max_phase) : undefined,
    smiles: d.smiles != null ? String(d.smiles) : undefined,
    type: d.molecule_type != null ? String(d.molecule_type) : undefined,
  }))

  const pc = search?.pubchem_compound
  const pubchem = pc
    ? {
        cid: String(pc.cid ?? ''),
        name: String(pc.title ?? pc.IUPACName ?? ''),
        mw: pc.molecular_weight != null ? Number(pc.molecular_weight) : undefined,
        formula: String(pc.molecular_formula ?? ''),
      }
    : null

  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="Drug Search"
        icon="💊"
        subtitle="Explore ChEMBL and PubChem compounds associated with a gene or drug name."
      >
        <AnalysisForm
          fields={[
            {
              key: 'query',
              label: 'Gene or drug name',
              placeholder: 'e.g. BRCA1, aspirin, olaparib',
              value: query,
              onChange: setQuery,
            },
          ]}
          onSubmit={run}
          loading={loading}
          disabled={!query}
          submitLabel="Search drugs"
        />
        <ErrorNotice error={error} />

        {loading ? (
          <div className="mt-6">
            <ResultSkeleton cards={2} />
          </div>
        ) : null}

        {search ? (
          <div className="mt-6 space-y-5">
            {drugs.length > 0 ? (
              <Reveal>
                <Card
                  title="ChEMBL Compounds"
                  icon="💊"
                  subtitle={`${drugs.length} matching compounds`}
                  action={<Chip tone="blue">ChEMBL</Chip>}
                >
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {drugs.map((d, i) => (
                      <div
                        key={`${d.id}-${i}`}
                        className="animate-fade-in-up rounded-xl border border-slate-100 bg-slate-50 p-4 transition hover:border-genome-200 hover:shadow-sm"
                        style={{ animationDelay: `${Math.min(i * 80, 400)}ms` }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-900">{d.name}</span>
                          {d.maxPhase != null ? <Chip tone="green">Phase {d.maxPhase}</Chip> : null}
                        </div>
                        <p className="mt-1 font-mono text-xs text-genome-700">{d.id}</p>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {d.type ? <Chip>{d.type}</Chip> : null}
                          {d.mw ? <Chip tone="amber">MW {d.mw.toFixed(1)}</Chip> : null}
                        </div>
                        {d.smiles ? (
                          <p className="mt-2 break-all font-mono text-[11px] text-slate-400">
                            {d.smiles}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </Card>
              </Reveal>
            ) : (
              <Reveal>
                <Card title="ChEMBL Compounds" icon="💊">
                  <p className="text-sm text-slate-400">No compounds found.</p>
                </Card>
              </Reveal>
            )}

            {pubchem?.cid ? (
              <Reveal delay={120}>
                <Card
                  title="PubChem Compound"
                  icon="🧪"
                  subtitle={`CID ${pubchem.cid}`}
                  action={<Chip tone="blue">PubChem</Chip>}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-slate-900">{pubchem.name || '—'}</span>
                    {pubchem.formula ? <Chip>{pubchem.formula}</Chip> : null}
                    {pubchem.mw ? <Chip tone="amber">MW {pubchem.mw.toFixed(1)}</Chip> : null}
                  </div>
                </Card>
              </Reveal>
            ) : null}
          </div>
        ) : null}
      </AnalysisLayout>
    </>
  )
}
