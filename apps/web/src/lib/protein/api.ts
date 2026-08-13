/**
 * Protein data adapter (Phase 6.5).
 *
 * Thin typed adapter over the existing GenomeAI protein endpoints:
 *
 *     GET /proteins/{protein_id}
 *     GET /proteins/
 *
 * It reuses the shared `API_BASE_URL`, `GenomeApiError`, and type-guard
 * helpers from `lib/genome/api.ts` and normalizes the (typed-on-the-backend,
 * untyped-on-the-wire) response into the viewer's `Protein` model.
 *
 * ## Feature boundary
 *
 * The backend exposes protein identity and sequence fields (`protein_id`,
 * `sequence`, `length`, ...) but **does not yet expose annotation features**
 * (domains, motifs, active sites, ...). `toProtein` therefore returns
 * `features: []`, and `toProteinFeature` provides the normalization seam a
 * future feature endpoint will use. The isolated development fixture in
 * `lib/protein/protein.fixtures.ts` supplies representative features today
 * and must be replaced, not treated as a real API. See
 * `docs/visualization/protein-viewer.md`.
 */

import { API_BASE_URL, GenomeApiError } from '@/lib/genome/api'
import { asNumber, asString, idOf } from '@/lib/genome/api'

import { normalizeFeatureType, prepareFeatures } from './features'
import { isValidSequence } from './sequence'
import type { Protein, ProteinFeature, ProteinFeatureType } from './types'

/** Raw record shape returned by the protein CRUD endpoints. */
export interface RawProteinRecord {
  id?: unknown
  protein_id?: unknown
  protein_name?: unknown
  symbol?: unknown
  accession?: unknown
  sequence?: unknown
  length?: unknown
  molecular_weight?: unknown
  organism?: unknown
  function?: unknown
  description?: unknown
  [key: string]: unknown
}

/** Raw record shape a future feature endpoint is expected to return. */
export interface RawProteinFeatureRecord {
  id?: unknown
  start?: unknown
  end?: unknown
  type?: unknown
  label?: unknown
  name?: unknown
  description?: unknown
  accession?: unknown
  metadata?: unknown
  [key: string]: unknown
}

function asMetadata(value: unknown): Record<string, string | number | boolean> | undefined {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return undefined
  const entries = Object.entries(value).filter(
    (entry): entry is [string, string | number | boolean] => {
      const [, field] = entry
      return typeof field === 'string' || typeof field === 'number' || typeof field === 'boolean'
    },
  )
  return entries.length > 0 ? Object.fromEntries(entries) : undefined
}

/**
 * Normalizes a raw feature record into a typed `ProteinFeature`. Invalid
 * spans are preserved with the values reported and must pass
 * `isValidFeature`/`prepareFeatures` before rendering.
 */
export function toProteinFeature(item: RawProteinFeatureRecord): ProteinFeature {
  const id = idOf(item.id)
  const start = asNumber(item.start)
  const end = asNumber(item.end)
  const type = normalizeFeatureType(asString(item.type) ?? 'custom')
  const label = asString(item.label) ?? asString(item.name) ?? ''
  const description = asString(item.description)
  const accession = asString(item.accession)
  const metadata = asMetadata(item.metadata)

  return {
    id,
    start: start ?? 0,
    end: end ?? 0,
    type: type as ProteinFeatureType,
    label,
    ...(description !== undefined ? { description } : {}),
    ...(accession !== undefined ? { accession } : {}),
    ...(metadata !== undefined ? { metadata } : {}),
  }
}

/**
 * Normalizes a raw protein record into the viewer's `Protein` model. The
 * reported `length` is used when present, otherwise it is derived from the
 * sequence. The backend does not yet expose features, so `features` is `[]`.
 */
export function toProtein(item: RawProteinRecord): Protein {
  const id = idOf(item.id) || asString(item.protein_id) || ''
  const sequence = asString(item.sequence) ?? ''
  const length = asNumber(item.length) ?? sequence.length
  const name =
    asString(item.symbol) || asString(item.protein_name) || asString(item.protein_id) || ''
  const description = asString(item.description) ?? asString(item.function)

  return {
    id,
    ...(asString(item.protein_id) !== undefined ? { proteinId: asString(item.protein_id) } : {}),
    name,
    sequence,
    length,
    ...(asString(item.organism) !== undefined ? { organism: asString(item.organism) } : {}),
    ...(description !== undefined ? { description } : {}),
    features: [],
  }
}

/** True when a normalized protein is usable for display. */
export function isValidProtein(protein: Protein): boolean {
  return protein.id.length > 0 && protein.length >= 1 && isValidSequence(protein.sequence)
}

/** Builds the URL used by `fetchProtein`. */
export function proteinUrl(proteinId: string): string {
  return `${API_BASE_URL}/proteins/${encodeURIComponent(proteinId)}`
}

/**
 * Fetches a single protein by id and normalizes it. Reuses the caller's
 * `AbortSignal` so the request cancels cleanly with the visualization data
 * lifecycle.
 */
export async function fetchProtein(proteinId: string, signal?: AbortSignal): Promise<Protein> {
  const response = await fetch(proteinUrl(proteinId), {
    headers: { 'Content-Type': 'application/json' },
    signal,
  })

  if (!response.ok) {
    throw new GenomeApiError(
      `GenomeAI API returned ${response.status} for protein ${proteinId}`,
      response.status,
    )
  }

  const payload = (await response.json()) as RawProteinRecord | null
  if (payload === null || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new GenomeApiError(`GenomeAI API returned an invalid payload for protein ${proteinId}`)
  }

  return toProtein(payload)
}

export interface FetchProteinsOptions {
  /** Cancellation signal forwarded to the request. */
  signal?: AbortSignal
  /** Supplies features until the backend exposes a feature endpoint. */
  featureSource?: (protein: Protein) => ProteinFeature[]
}

/**
 * Fetches the protein catalog and returns the normalized, valid records. A
 * feature source can be supplied until the backend exposes annotations; it
 * only enriches when the API did not already provide features.
 */
export async function fetchProteins(options: FetchProteinsOptions = {}): Promise<Protein[]> {
  const response = await fetch(`${API_BASE_URL}/proteins/`, {
    headers: { 'Content-Type': 'application/json' },
    signal: options.signal,
  })

  if (!response.ok) {
    throw new GenomeApiError(`GenomeAI API returned ${response.status} for the protein catalog`)
  }

  const payload = (await response.json()) as unknown[] | null
  if (payload === null || !Array.isArray(payload)) {
    throw new GenomeApiError('GenomeAI API returned an invalid protein catalog payload')
  }

  const featureSource = options.featureSource ?? (() => [])
  return payload
    .filter((value): value is RawProteinRecord => typeof value === 'object' && value !== null)
    .map((record) => toProtein(record))
    .filter(isValidProtein)
    .map((protein) => ({
      ...protein,
      features:
        protein.features.length > 0 ? protein.features : prepareFeatures(featureSource(protein)),
    }))
}
