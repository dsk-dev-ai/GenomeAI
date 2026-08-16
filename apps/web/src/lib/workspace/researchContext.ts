/**
 * Research workspace contexts (Phase 6.9).
 *
 * A research context is the shared genomic region that the context-aware
 * workspace panels (Genome Browser, Gene / Transcript viewer) follow when it
 * changes. Presets live here so the workspace UI and its tests share one
 * source of truth; the coordinates mirror the Phase 6.2/6.3 demo regions.
 *
 * Relationship and analysis panels (network, protein, expression, heatmap,
 * volcano, coverage, distribution) are not region-driven: their datasets are
 * TP53-pathway fixtures, so they render the same analysis for every context.
 * See `docs/visualization/workspace.md` for this fixture boundary.
 */

import { formatRegionLabel } from '@/lib/genome/geometry'
import type { GenomeViewport, GenomicInterval } from '@/lib/genome/types'

/** A research context: a human-readable label plus a shared genomic region. */
export interface ResearchContext {
  /** Stable identifier (a preset id or a generated custom-region id). */
  id: string
  /** Human-readable label shown in the workspace selector. */
  label: string
  /** Optional supporting text shown beneath the label. */
  description?: string
  /** Shared one-based-inclusive region that drives context-aware panels. */
  region: GenomeViewport
}

/** Coordinates of the Phase 6.3 TP53 demo window (chr17). */
const TP53_LOCUS = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 } as const

/** Coordinates of the Phase 6.3 BRCA1-like fixture gene (chr17). */
const BRCA1_LOCUS = { chromosome: 'chr17', start: 43_044_295, end: 43_125_483 } as const

export const TP53_CONTEXT: ResearchContext = {
  id: 'tp53-locus',
  label: 'TP53 locus (chr17)',
  description:
    'A TP53-centred workspace: genome window, TP53 isoforms, interaction network, P53 protein, and TP53-pathway expression analyses.',
  region: { ...TP53_LOCUS },
}

export const BRCA1_CONTEXT: ResearchContext = {
  id: 'brca1-locus',
  label: 'BRCA1 locus (chr17)',
  description:
    'A BRCA1-centred workspace: genome window and the reverse-strand BRCA1 gene model. Relationship and analysis panels still show the TP53-pathway fixtures (fixture boundary).',
  region: { ...BRCA1_LOCUS },
}

/** Preset contexts offered by the workspace selector. */
export const PRESET_CONTEXTS: readonly ResearchContext[] = [TP53_CONTEXT, BRCA1_CONTEXT]

/** Returns the preset context with the given id, or `undefined`. */
export function researchContextById(id: string): ResearchContext | undefined {
  return PRESET_CONTEXTS.find((context) => context.id === id)
}

/** Converts a one-based inclusive interval to a viewport (no bounds metadata). */
export function regionToViewport(interval: GenomicInterval): GenomeViewport {
  return { chromosome: interval.chromosome, start: interval.start, end: interval.end }
}

/**
 * A stable, display-independent key for a context region, used to remount
 * context-aware panels when the region changes.
 */
export function contextRegionKey(region: GenomeViewport): string {
  return `${region.chromosome}:${region.start}-${region.end}`
}

/** Builds a custom context from a validated region interval. */
export function customContextFromInterval(interval: GenomicInterval): ResearchContext {
  const region = regionToViewport(interval)
  return {
    id: `custom-${region.chromosome}-${region.start}-${region.end}`,
    label: formatRegionLabel(region.chromosome, region.start, region.end),
    description: 'A custom region loaded from the region input.',
    region,
  }
}
