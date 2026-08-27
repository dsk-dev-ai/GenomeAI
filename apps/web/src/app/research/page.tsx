import { AnalysisLayout } from '@/components/research/AnalysisLayout'
import { ResearchNav } from '@/components/research/ResearchNav'
import Link from 'next/link'

const domains = [
  { href: '/research/gene', title: 'Gene', desc: 'NCBI gene annotations + function', emoji: '🧬' },
  {
    href: '/research/variant',
    title: 'Variant',
    desc: 'ClinVar + gnomAD + VEP pathogenicity',
    emoji: '🧪',
  },
  {
    href: '/research/protein',
    title: 'Protein',
    desc: 'UniProt + PDB + AlphaFold structure',
    emoji: '🔬',
  },
  {
    href: '/research/literature',
    title: 'Literature',
    desc: 'Europe PMC + Semantic Scholar papers',
    emoji: '📚',
  },
  { href: '/research/drug', title: 'Drug', desc: 'ChEMBL + PubChem drug targets', emoji: '💊' },
  {
    href: '/research/pathway',
    title: 'Pathway',
    desc: 'Reactome + STRING + KEGG pathways',
    emoji: '🛣️',
  },
  { href: '/research/disease', title: 'Disease', desc: 'OpenTargets + DO + Monarch', emoji: '🩺' },
  {
    href: '/research/report',
    title: 'Report',
    desc: 'Multi-domain executive summary',
    emoji: '📊',
  },
]

export default function ResearchHome() {
  return (
    <>
      <ResearchNav />
      <AnalysisLayout
        title="GenomeAI Research"
        subtitle="Free genomics intelligence across 8 domains — powered by 21 free APIs and Gemini AI"
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {domains.map((d) => (
            <Link
              key={d.href}
              href={d.href}
              className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:border-blue-400 hover:shadow"
            >
              <div className="text-2xl">{d.emoji}</div>
              <h2 className="mt-2 font-semibold text-gray-900">{d.title}</h2>
              <p className="mt-1 text-sm text-gray-600">{d.desc}</p>
            </Link>
          ))}
        </div>
      </AnalysisLayout>
    </>
  )
}
