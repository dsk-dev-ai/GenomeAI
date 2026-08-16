/**
 * Development fixtures for the Genome Browser demo (Phase 6.2).
 *
 * The GenomeAI backend serves the Phase 5 coordinate-search API that the
 * Genome Browser normally talks to (`lib/genome/api.ts`). This module
 * provides small, clearly isolated, typed fixtures that mimic what that API
 * returns for the shared TP53 neighbourhood, so the demo renders data even
 * without a running backend. Loaders flow through the same `useGenomeTrack`
 * data lifecycle as the real adapter, keeping the seam production-shaped.
 *
 * ## Boundary
 *
 * These are **development fixtures, not a real API** and not scientific fact.
 * Gene spans and variant positions below are illustrative of the viewer's
 * feature model and must be replaced by real GenomeAI search results. See
 * `docs/visualization/genome-browser.md`.
 */

import type { GenomicFeature, VariantFeature } from './types'

/** Genes in the shared TP53 window (chr17:7,650,000-7,700,000). */
const TP53_REGION_GENES: GenomicFeature[] = [
  {
    id: 'gene-tp53',
    type: 'gene',
    chromosome: 'chr17',
    start: 7_665_901,
    end: 7_690_000,
    strand: '+',
    name: 'TP53',
    metadata: { geneId: 'ENSG00000141510', biotype: 'protein_coding' },
  },
  {
    id: 'gene-atp5mc1',
    type: 'gene',
    chromosome: 'chr17',
    start: 7_653_000,
    end: 7_657_500,
    strand: '-',
    name: 'ATP5MC1',
    metadata: { geneId: 'ENSG00000169174', biotype: 'protein_coding' },
  },
  {
    id: 'gene-lrrc37a2',
    type: 'gene',
    chromosome: 'chr17',
    start: 7_698_000,
    end: 7_700_000,
    strand: '+',
    name: 'LRRC37A2',
    metadata: { geneId: 'ENSG00000261604', biotype: 'protein_coding' },
  },
]

/** Point variants in the shared TP53 window (single-position model). */
const TP53_REGION_VARIANTS: VariantFeature[] = [
  {
    id: 'variant-tp53-r175h',
    type: 'variant',
    chromosome: 'chr17',
    start: 7_678_534,
    end: 7_678_534,
    position: 7_678_534,
    ref: 'G',
    alt: 'A',
    name: 'G>A',
    variantId: 'COSM10660',
    variantType: 'snv',
    quality: 214,
    filterStatus: 'PASS',
    geneId: 'gene-tp53',
    description: 'Pathogenic TP53 missense variant R175H',
  },
  {
    id: 'variant-tp53-r248q',
    type: 'variant',
    chromosome: 'chr17',
    start: 7_677_306,
    end: 7_677_306,
    position: 7_677_306,
    ref: 'G',
    alt: 'A',
    name: 'G>A',
    variantId: 'COSM10662',
    variantType: 'snv',
    quality: 198,
    filterStatus: 'PASS',
    geneId: 'gene-tp53',
    description: 'Pathogenic TP53 missense variant R248Q',
  },
  {
    id: 'variant-tp53-p151s',
    type: 'variant',
    chromosome: 'chr17',
    start: 7_678_560,
    end: 7_678_560,
    position: 7_678_560,
    ref: 'C',
    alt: 'T',
    name: 'C>T',
    variantId: 'COSM10665',
    variantType: 'snv',
    quality: 142,
    filterStatus: 'PASS',
    geneId: 'gene-tp53',
    description: 'Pathogenic TP53 missense variant P151S',
  },
]

/** Genes for the TP53 window, filtered to an overlapping interval. */
export function fixtureIntervalGenes(interval: {
  chromosome: string
  start: number
  end: number
}): GenomicFeature[] {
  return TP53_REGION_GENES.filter(
    (gene) =>
      gene.chromosome === interval.chromosome &&
      gene.end >= interval.start &&
      gene.start <= interval.end,
  )
}

/** Variants for the TP53 window, filtered to an overlapping interval. */
export function fixtureIntervalVariants(interval: {
  chromosome: string
  start: number
  end: number
}): VariantFeature[] {
  return TP53_REGION_VARIANTS.filter(
    (variant) =>
      variant.chromosome === interval.chromosome &&
      variant.position >= interval.start &&
      variant.position <= interval.end,
  )
}
