import { post } from './client'

export interface PDBInfo {
  pdb_id: string
  title: string
  method: string
  resolution: number
}

export interface AlphaFoldInfo {
  alphafold_id: string
  sequence_length: number
  confidence_version: string
}

export interface ProteinAnalysis {
  protein_name: string
  accession: string
  gene_names: string[]
  organism: string
  length: number
  function: string
  subcellular_location: string
  pdb_structures: PDBInfo[]
  alphafold: AlphaFoldInfo | null
  function_summary: string
  domains: string[]
  clinical_significance: string
  drug_targets: string[]
  disease_associations: string[]
  structural_notes: string
  data_sources: string[]
}

export function analyzeProtein(gene: string): Promise<ProteinAnalysis> {
  return post<ProteinAnalysis>('/api/v1/proteins/analyze', { gene })
}
