import { post } from './client'

export interface DrugSearch {
  query: string
  chembl_drugs: Record<string, unknown>[]
  pubchem_compound: Record<string, unknown> | null
}

export function searchDrugs(query: string): Promise<DrugSearch> {
  return post<DrugSearch>('/api/v1/drugs/search', { query })
}
