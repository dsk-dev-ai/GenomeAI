import { post } from './client'

export interface GeneAnalysis {
  gene_symbol: string
  gene_id: string
  name: string
  organism: string
  chromosome: string
  map_location: string
  description: string
  aliases: string[]
  gene_type: string
  function: string
  key_variants: string[]
  associated_diseases: string[]
  drug_targets: string[]
  clinical_significance: string
  summary: string
  source: string
}

export function analyzeGene(symbol: string, organism = 'Homo sapiens'): Promise<GeneAnalysis> {
  return post<GeneAnalysis>('/api/v1/genes/analyze', { symbol, organism })
}
