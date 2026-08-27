import { post } from './client'

export interface ClinVarInfo {
  clinvar_id: string
  clinical_significance: string
  review_status: string
  condition: string
  hgvs_c: string
  hgvs_p: string
}

export interface GnomADInfo {
  variant_id: string
  allele_frequency: number
  allele_count: number
  allele_number: number
}

export interface VEPInfo {
  consequence: string
  impact: string
  sift_prediction: string
  sift_score: number | null
  polyphen_prediction: string
  polyphen_score: number | null
}

export interface VariantInterpretation {
  variant_description: string
  gene_symbol: string
  clinvar: ClinVarInfo | null
  gnomad: GnomADInfo | null
  vep: VEPInfo | null
  pathogenicity: string
  acmg_criteria: string[]
  reasoning: string
  clinical_actionability: string
  summary: string
  data_sources: string[]
}

export function interpretVariant(
  gene: string,
  hgvs_c = '',
  clinvar_id = '',
): Promise<VariantInterpretation> {
  return post<VariantInterpretation>('/api/v1/variants/interpret', {
    gene,
    hgvs_c,
    clinvar_id,
  })
}
