import { post } from './client'

export interface DiseaseAnalysisRequest {
  query: string
  genes?: string[]
}

export interface DiseaseInfo {
  disease_id: string
  name: string
  description: string
}

export interface GeneDiseaseAssociation {
  gene_symbol: string
  gene_id: string
  disease_name: string
  disease_id: string
  score: number
}

export interface MonarchDiseaseResult {
  disease_id: string
  disease_name: string
  category: string
}

export interface DiseaseAnalysis {
  query: string
  diseases: DiseaseInfo[]
  gene_disease_associations: GeneDiseaseAssociation[]
  monarch_results: MonarchDiseaseResult[]
  ai_analysis: string
  sources: string[]
}

export function searchDiseases(query: string): Promise<DiseaseAnalysis> {
  return post<DiseaseAnalysis>('/api/v1/diseases/search', {
    query,
  } as DiseaseAnalysisRequest)
}

export function analyzeGeneDiseases(gene: string): Promise<DiseaseAnalysis> {
  return post<DiseaseAnalysis>('/api/v1/diseases/gene', {
    query: gene,
  } as DiseaseAnalysisRequest)
}
