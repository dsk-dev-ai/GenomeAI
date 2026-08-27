import { post } from './client'

export interface PathwayAnalysisRequest {
  gene: string
  genes?: string[]
}

export interface PathwayInfo {
  name: string
  st_id?: string
  pathway_id?: string
  species?: string
}

export interface InteractionInfo {
  partner: string
  from_gene: string
  to_gene: string
  score: number
}

export interface EnrichmentInfo {
  category: string
  term: string
  description: string
  p_value: number
  fdr: number
}

export interface PathwayAnalysis {
  query: string
  reactome_pathways: PathwayInfo[]
  kegg_pathways: PathwayInfo[]
  string_interactions: InteractionInfo[]
  string_enrichment: EnrichmentInfo[]
  ai_analysis: string
  sources: string[]
}

export function analyzePathway(gene: string, genes: string[] = []): Promise<PathwayAnalysis> {
  return post<PathwayAnalysis>('/api/v1/pathways/analyze', {
    gene,
    genes,
  } as PathwayAnalysisRequest)
}
