import { post } from './client'

export interface MultiDomainReportRequest {
  gene: string
  variant?: string
}

export interface DomainReport {
  summary: string
  data: Record<string, unknown>
}

export interface MultiDomainReport {
  gene: string
  gene_report: DomainReport
  variant_report: DomainReport
  protein_report: DomainReport
  literature_report: DomainReport & { paper_count?: number }
  drug_report: DomainReport & { drug_count?: number }
  pathway_report: DomainReport
  disease_report: DomainReport
  executive_summary: string
  sources: string[]
}

export function generateReport(gene: string, variant = ''): Promise<MultiDomainReport> {
  return post<MultiDomainReport>('/api/v1/reports/multi-domain', {
    gene,
    variant,
  } as MultiDomainReportRequest)
}
