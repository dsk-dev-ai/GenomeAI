/**
 * Protein feature model (Phase 6.5).
 *
 * Normalization, validation, deterministic ordering, and display helpers for
 * annotation features. The viewer is deliberately generic: it understands a
 * small set of common feature classes for default presentation but carries
 * any other type string verbatim, so it is not hard-wired to one biological
 * database.
 *
 * Coordinates are 1-based inclusive (see `lib/protein/types.ts`).
 */

import type { KnownProteinFeatureType, ProteinFeature, ProteinFeatureType } from './types'

/** Common annotation classes with default presentation colours. */
const KNOWN_TYPES: readonly KnownProteinFeatureType[] = [
  'domain',
  'motif',
  'active_site',
  'binding_site',
  'signal_peptide',
  'transmembrane',
  'secondary_structure',
  'region',
  'custom',
]

const TYPE_COLORS: Record<KnownProteinFeatureType, string> = {
  domain: '#2563eb',
  motif: '#16a34a',
  active_site: '#dc2626',
  binding_site: '#7c3aed',
  signal_peptide: '#d97706',
  transmembrane: '#db2777',
  secondary_structure: '#0d9488',
  region: '#64748b',
  custom: '#94a3b8',
}

/** Fallback colour for feature types this viewer does not special-case. */
const DEFAULT_TYPE_COLOR = '#94a3b8'

/**
 * Normalizes an arbitrary type string: trims it and maps to a known class
 * when it matches, otherwise preserves the string verbatim.
 */
export function normalizeFeatureType(type: string): ProteinFeatureType {
  const trimmed = type.trim()
  if (trimmed.length === 0) return 'custom'
  const known = KNOWN_TYPES.find((candidate) => candidate === trimmed)
  return known ?? trimmed
}

/** Default fill colour for a feature class. */
export function featureTypeColor(type: ProteinFeatureType): string {
  if (KNOWN_TYPES.includes(type as KnownProteinFeatureType)) {
    return TYPE_COLORS[type as KnownProteinFeatureType]
  }
  return DEFAULT_TYPE_COLOR
}

/** Human-readable label for a feature class. */
export function featureTypeLabel(type: ProteinFeatureType): string {
  return type.replaceAll('_', ' ')
}

/** True when a feature carries a usable 1-based residue span + identity. */
export function isValidFeature(feature: ProteinFeature, length?: number): boolean {
  if (feature.id.length === 0) return false
  if (!Number.isSafeInteger(feature.start) || !Number.isSafeInteger(feature.end)) return false
  if (feature.start < 1 || feature.end < feature.start) return false
  if (length !== undefined && feature.end > length) return false
  return true
}

/** Deterministic display order: by start, then end, then id. */
export function sortFeatures(features: readonly ProteinFeature[]): ProteinFeature[] {
  return [...features].sort(
    (a, b) => a.start - b.start || a.end - b.end || a.id.localeCompare(b.id),
  )
}

/** Removes duplicate ids, keeping the first occurrence in display order. */
export function dedupeFeatures(features: readonly ProteinFeature[]): ProteinFeature[] {
  const seen = new Set<string>()
  const result: ProteinFeature[] = []
  for (const feature of features) {
    if (seen.has(feature.id)) continue
    seen.add(feature.id)
    result.push(feature)
  }
  return result
}

/**
 * Validates, de-duplicates, and orders features for display. Invalid or
 * duplicate records are dropped so rendering never receives them.
 */
export function prepareFeatures(
  features: readonly ProteinFeature[],
  length?: number,
): ProteinFeature[] {
  return dedupeFeatures(sortFeatures(features.filter((feature) => isValidFeature(feature, length))))
}

/** Short display label for a feature bar. */
export function featureLabel(feature: ProteinFeature): string {
  if (feature.label.length > 0) return feature.label
  return `${featureTypeLabel(feature.type)} ${feature.start}-${feature.end}`
}

/** Accessible name for a feature's selection control. */
export function featureAccessibleLabel(feature: ProteinFeature): string {
  return `${featureLabel(feature)}, residues ${feature.start}-${feature.end}, ${featureTypeLabel(feature.type)}`
}

/** Labelled detail rows shown in the selected-feature panel. */
export function featureDetailLines(
  feature: ProteinFeature,
): Array<{ label: string; value: string }> {
  const lines: Array<{ label: string; value: string }> = []
  lines.push({ label: 'Type', value: featureTypeLabel(feature.type) })
  lines.push({ label: 'Residues', value: `${feature.start}-${feature.end}` })
  if (feature.description) lines.push({ label: 'Description', value: feature.description })
  if (feature.accession) lines.push({ label: 'Accession', value: feature.accession })
  if (feature.metadata) {
    for (const [key, value] of Object.entries(feature.metadata)) {
      if (value !== undefined && value !== null && value !== '') {
        lines.push({ label: key, value: String(value) })
      }
    }
  }
  return lines
}
