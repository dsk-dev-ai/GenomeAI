/**
 * Expression dataset data adapter (Phase 6.7).
 *
 * Defines the raw record shapes a future GenomeAI expression endpoint is
 * expected to return and the normalization seam (`toExpressionPoint`,
 * `toExpressionSeries`, `expressionDatasetFromRecords`) the chart uses. It
 * reuses the shared `API_BASE_URL`, `GenomeApiError`, and guard helpers from
 * `lib/genome/api.ts`, and the deterministic normalizer from
 * `lib/scientific/expression.ts`.
 *
 * ## API limitation
 *
 * The GenomeAI backend does **not** yet expose an expression endpoint. This
 * module documents the expected contract and `fetchExpressionDataset` attempts
 * `GET /expression/datasets/{id}` (which will 404 today, surfacing the
 * limitation as a typed error). The demo therefore uses the isolated
 * deterministic fixtures in `lib/scientific/expression.fixtures.ts` and flips
 * to the real adapter as soon as an expression endpoint exists. See
 * `docs/visualization/scientific-charts.md`.
 *
 * The browser never talks to external biological databases (GEO, ArrayExpress,
 * TCGA, ...); those feed GenomeAI through the later connector/ingestion
 * architecture.
 */

import { API_BASE_URL, GenomeApiError, asNumber, asString } from '@/lib/genome/api'

import { normalizeExpressionDataset, sanitizeMetadata } from './expression'
import type { ExpressionDataset, ExpressionPoint, ExpressionSeries } from './types'

/** Raw record shape a future expression endpoint is expected to return. */
export interface RawExpressionDatasetRecord {
  id?: unknown
  title?: unknown
  series?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/** Raw series record shape. */
export interface RawExpressionSeriesRecord {
  id?: unknown
  label?: unknown
  points?: unknown
  [key: string]: unknown
}

/** Raw point record shape. */
export interface RawExpressionPointRecord {
  identifier?: unknown
  sample?: unknown
  value?: unknown
  normalized_value?: unknown
  normalizedValue?: unknown
  metadata?: unknown
  [key: string]: unknown
}

function recordIsObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** Normalizes a raw point record into an `ExpressionPoint`, or `undefined`. */
export function toExpressionPoint(record: unknown): ExpressionPoint | undefined {
  if (!recordIsObject(record)) return undefined
  const identifier = asString(record.identifier)
  const sample = asString(record.sample)
  const value = asNumber(record.value)
  if (identifier === undefined || identifier.length === 0) return undefined
  if (sample === undefined || sample.length === 0) return undefined
  if (value === undefined || !Number.isFinite(value)) return undefined
  const normalizedValue = asNumber(record.normalized_value) ?? asNumber(record.normalizedValue)
  return {
    identifier,
    sample,
    value,
    ...(normalizedValue !== undefined && Number.isFinite(normalizedValue)
      ? { normalizedValue }
      : {}),
    ...(sanitizeMetadata(record.metadata) !== undefined
      ? { metadata: sanitizeMetadata(record.metadata) }
      : {}),
  }
}

/** Normalizes a raw series record into an `ExpressionSeries`, or `undefined`. */
export function toExpressionSeries(record: unknown): ExpressionSeries | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  const label = asString(record.label)
  if (id === undefined || id.length === 0) return undefined
  if (label === undefined || label.length === 0) return undefined
  const rawPoints = Array.isArray(record.points) ? record.points : []
  const points = rawPoints
    .map(toExpressionPoint)
    .filter((point): point is ExpressionPoint => point !== undefined)
  return { id, label, points }
}

/**
 * Builds a normalized, deterministic `ExpressionDataset` from raw records.
 * Invalid records are dropped via `toExpressionPoint`/`toExpressionSeries`;
 * `normalizeExpressionDataset` then dedupes identifiers, drops invalid
 * points/series, and orders canonically.
 */
export function expressionDatasetFromRecords(record: unknown): ExpressionDataset | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const title = asString(record.title) ?? `Expression dataset ${id}`
  const rawSeries = Array.isArray(record.series) ? record.series : []
  const series = rawSeries
    .map(toExpressionSeries)
    .filter((candidate): candidate is ExpressionSeries => candidate !== undefined)
  return normalizeExpressionDataset({
    id,
    title,
    series,
    ...(sanitizeMetadata(record.metadata) !== undefined
      ? { metadata: sanitizeMetadata(record.metadata) }
      : {}),
  })
}

/**
 * Fetches an expression dataset by id from the (not-yet-existing) expression
 * endpoint. Throws `GenomeApiError` on failure today so the limitation is
 * explicit and typed. Fixture-based demos bypass this loader.
 */
export async function fetchExpressionDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<ExpressionDataset> {
  const response = await fetch(
    `${API_BASE_URL}/expression/datasets/${encodeURIComponent(datasetId)}`,
    {
      headers: { 'Content-Type': 'application/json' },
      signal,
    },
  )
  if (!response.ok) {
    throw new GenomeApiError(
      `GenomeAI API returned ${response.status} for expression dataset ${datasetId}`,
      response.status,
    )
  }
  const payload: unknown = await response.json()
  const dataset = expressionDatasetFromRecords(payload)
  if (dataset === undefined) {
    throw new GenomeApiError(
      `GenomeAI API returned an invalid payload for expression dataset ${datasetId}`,
    )
  }
  return dataset
}
