import { post } from './client'

export interface LiteratureSearch {
  query: string
  europepmc_count: number
  semanticscholar_count: number
  europepmc_articles: Record<string, unknown>[]
  semanticscholar_papers: Record<string, unknown>[]
}

export function searchLiterature(query: string, max_results = 10): Promise<LiteratureSearch> {
  return post<LiteratureSearch>('/api/v1/literature/search', { query, max_results })
}

export interface LiteratureAnalysis {
  query: string
  papers_count: number
  ai_analysis: string | Record<string, unknown> | null
  error: string | null
}

export function analyzeLiterature(query: string, max_results = 5): Promise<LiteratureAnalysis> {
  return post<LiteratureAnalysis>('/api/v1/literature/analyze', { query, max_results })
}
