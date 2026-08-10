/**
 * Variant domain model (Phase 6.4).
 *
 * Variants in the GenomeAI data model are **single-position** records:
 * the coordinate-search API returns one 1-based `position` (there is no
 * `end_position` and no strand). This module defines the typed surface the
 * variant visualization consumes, reusing the existing `VariantFeature`
 * type from `lib/genome/types.ts`, and provides the pure helpers (label
 * formatting, accessibility text, validation) that the renderer builds on.
 *
 * ## Type representation
 *
 * The API exposes `type` as a free-form, nullable string (e.g. `snv`) with
 * no enumerated vocabulary on the backend. The model therefore carries it
 * as opaque text and renders it verbatim — it never infers a variant class
 * from arbitrary strings or from `ref`/`alt` lengths. `ref > alt` is used
 * only as a display convenience, never as a classification.
 */

import type { RawSearchItem } from './api'
import type { VariantFeature } from './types'

/** The typed variant record used by the variant visualization. */
export type Variant = VariantFeature

function asString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined
}

function asNumber(value: unknown): number | undefined {
  return typeof value === 'number' ? value : undefined
}

function idOf(value: unknown): string {
  if (typeof value === 'string' && value.length > 0) return value
  if (typeof value === 'object' && value !== null && 'id' in value) {
    return idOf((value as { id: unknown }).id)
  }
  return ''
}

/**
 * Normalizes a raw variant record from the coordinate-search API.
 *
 * Mirrors `toVariantFeature` in `lib/genome/api.ts` so the model module is
 * self-contained; the shared request pipeline remains in `api.ts`.
 */
export function toVariant(item: RawSearchItem): Variant {
  const position = asNumber(item.position)
  const chromosome = asString(item.chromosome)
  if (chromosome === undefined || position === undefined || position < 1) {
    return { id: '', type: 'variant', chromosome: '', start: 0, end: 0, position: 0 }
  }
  const ref = asString(item.ref)
  const alt = asString(item.alt)
  const quality = asNumber(item.quality)
  return {
    id: idOf(item.id) || asString(item.variant_id) || '',
    type: 'variant',
    chromosome,
    start: position,
    end: position,
    position,
    ref,
    alt,
    name: ref && alt ? `${ref}>${alt}` : undefined,
    variantId: asString(item.variant_id),
    variantType: asString(item.type),
    ...(quality !== undefined ? { quality } : {}),
    filterStatus: asString(item.filter_status),
    geneId: asString(item.gene_id),
    description: asString(item.description),
  }
}

/** True when `variant` carries a usable 1-based point coordinate. */
export function isValidVariant(variant: Variant): boolean {
  return (
    variant.chromosome.length > 0 && Number.isSafeInteger(variant.position) && variant.position >= 1
  )
}

/**
 * Short display label for a variant: `ref>alt` when both alleles are known,
 * otherwise the accession (`variantId`) or the internal id.
 */
export function variantLabel(variant: Variant): string {
  if (variant.ref && variant.alt) return `${variant.ref}>${variant.alt}`
  if (variant.variantId) return variant.variantId
  return variant.id || `${variant.chromosome}:${variant.position}`
}

/**
 * Accessible name describing one variant, e.g.
 * `C>T at chr17:7,688,456 (rs113488022, snv)`.
 */
export function variantAccessibleLabel(variant: Variant): string {
  const parts = [
    variantLabel(variant),
    `${variant.chromosome}:${variant.position.toLocaleString('en-US')}`,
  ]
  if (variant.variantType) parts.push(variant.variantType)
  if (variant.filterStatus) parts.push(`filter ${variant.filterStatus}`)
  return parts.join(', ')
}

/** A labelled detail line shown in the variant detail panel. */
export interface VariantDetailLine {
  label: string
  value: string
}

/**
 * Readable detail lines for a selected variant. Only fields the API
 * actually reports are included, in a stable order.
 */
export function variantDetailLines(variant: Variant): VariantDetailLine[] {
  const lines: VariantDetailLine[] = [
    {
      label: 'Position',
      value: `${variant.chromosome}:${variant.position.toLocaleString('en-US')}`,
    },
  ]
  if (variant.ref || variant.alt) {
    lines.push({ label: 'Alleles', value: `${variant.ref ?? '?'}>${variant.alt ?? '?'}` })
  }
  if (variant.variantType) lines.push({ label: 'Type', value: variant.variantType })
  if (variant.quality !== undefined) {
    lines.push({ label: 'Quality', value: String(variant.quality) })
  }
  if (variant.filterStatus) lines.push({ label: 'Filter', value: variant.filterStatus })
  if (variant.variantId) lines.push({ label: 'Accession', value: variant.variantId })
  if (variant.geneId) lines.push({ label: 'Gene', value: variant.geneId })
  if (variant.description) lines.push({ label: 'Description', value: variant.description })
  return lines
}
