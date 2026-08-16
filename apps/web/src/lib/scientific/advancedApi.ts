/**
 * Advanced scientific chart data adapters (Phase 6.8).
 *
 * Defines the raw record shapes future GenomeAI endpoints are expected to
 * return for heatmap, volcano, coverage, and distribution data, plus the
 * normalization seams (`*FromRecords`) each chart uses. It reuses the shared
 * `API_BASE_URL`, `GenomeApiError`, and guard helpers from
 * `lib/genome/api.ts`, and the deterministic normalizers from
 * `lib/scientific/{heatmap,volcano,coverage,distribution}.ts`.
 *
 * ## API limitation
 *
 * The GenomeAI backend does **not** yet expose any of these endpoints. This
 * module documents the expected contracts and the `fetch*Dataset` helpers
 * attempt `GET /advanced/...` URLs (which will 404 today, surfacing the
 * limitation as a typed error). The demos therefore use the isolated
 * deterministic fixtures in `lib/scientific/advanced.fixtures.ts` and flip to
 * the real adapters as soon as the endpoints exist. See
 * `docs/visualization/advanced-scientific-charts.md`.
 */

import { API_BASE_URL, GenomeApiError, asNumber, asString } from '@/lib/genome/api'

import type {
  CoverageBin,
  CoverageDataset,
  DistributionDataset,
  DistributionValue,
  HeatmapDataset,
  VolcanoDataset,
  VolcanoPoint,
} from './advancedTypes'
import { normalizeCoverageDataset } from './coverage'
import { normalizeDistributionDataset } from './distribution'
import { sanitizeMetadata } from './expression'
import { normalizeHeatmapDataset } from './heatmap'
import type { ScientificMetadata } from './types'
import { normalizeVolcanoDataset } from './volcano'

function recordIsObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((entry): entry is string => typeof entry === 'string')
    : []
}

/** Optional metadata carried by a record, coerced to safe scalars. */
function optionalMetadata(record: Record<string, unknown>): ScientificMetadata | undefined {
  return sanitizeMetadata(record.metadata)
}

export interface RawHeatmapRecord {
  id?: unknown
  title?: unknown
  rows?: unknown
  columns?: unknown
  values?: unknown
  row_labels?: unknown
  column_labels?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/**
 * Builds a normalized, deterministic `HeatmapDataset` from raw records.
 * Invalid rows/columns are dropped and the value matrix is re-arranged to the
 * normalized axis order; `normalizeHeatmapDataset` handles dedup and ordering.
 */
export function heatmapFromRecords(record: unknown): HeatmapDataset | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const title = asString(record.title) ?? 'Heatmap'
  const rows = asStringArray(record.rows)
  const columns = asStringArray(record.columns)
  const rawValues = Array.isArray(record.values) ? record.values : []
  const values = rawValues.map((row) => (Array.isArray(row) ? row.map(toOptionalFinite) : []))
  const rowLabels = toLabelMap(record.row_labels)
  const columnLabels = toLabelMap(record.column_labels)
  return normalizeHeatmapDataset({
    id,
    title,
    rows,
    columns,
    values,
    ...(rowLabels !== undefined ? { rowLabels } : {}),
    ...(columnLabels !== undefined ? { columnLabels } : {}),
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  })
}

function toOptionalFinite(value: unknown): number | undefined {
  const parsed = asNumber(value)
  return parsed !== undefined && Number.isFinite(parsed) ? parsed : undefined
}

function toLabelMap(value: unknown): Record<string, string> | undefined {
  if (!recordIsObject(value)) return undefined
  const entries = Object.entries(value).filter(
    (entry): entry is [string, string] => typeof entry[1] === 'string',
  )
  return entries.length > 0 ? Object.fromEntries(entries) : undefined
}

export interface RawVolcanoRecord {
  id?: unknown
  title?: unknown
  points?: unknown
  metadata?: unknown
  [key: string]: unknown
}

export interface RawVolcanoPointRecord {
  identifier?: unknown
  effect_size?: unknown
  effectSize?: unknown
  significance?: unknown
  adjusted_significance?: unknown
  adjustedSignificance?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/** Normalizes a raw volcano point record, or `undefined` when invalid. */
export function toVolcanoPoint(record: unknown): VolcanoPoint | undefined {
  if (!recordIsObject(record)) return undefined
  const identifier = asString(record.identifier)
  const effectSize = asNumber(record.effect_size) ?? asNumber(record.effectSize)
  const significance = asNumber(record.significance)
  if (identifier === undefined || identifier.length === 0) return undefined
  if (effectSize === undefined || !Number.isFinite(effectSize)) return undefined
  if (significance === undefined || !Number.isFinite(significance)) return undefined
  const adjusted = asNumber(record.adjusted_significance) ?? asNumber(record.adjustedSignificance)
  return {
    identifier,
    effectSize,
    significance,
    ...(adjusted !== undefined && Number.isFinite(adjusted)
      ? { adjustedSignificance: adjusted }
      : {}),
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  }
}

/** Builds a normalized `VolcanoDataset` from raw records. */
export function volcanoFromRecords(record: unknown): VolcanoDataset | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const title = asString(record.title) ?? 'Volcano plot'
  const rawPoints = Array.isArray(record.points) ? record.points : []
  const points = rawPoints
    .map(toVolcanoPoint)
    .filter((point): point is VolcanoPoint => point !== undefined)
  return normalizeVolcanoDataset({
    id,
    title,
    points,
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  })
}

export interface RawCoverageRecord {
  id?: unknown
  title?: unknown
  bins?: unknown
  metadata?: unknown
  [key: string]: unknown
}

export interface RawCoverageBinRecord {
  chromosome?: unknown
  start?: unknown
  end?: unknown
  coverage?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/** Normalizes a raw coverage bin record, or `undefined` when invalid. */
export function toCoverageBin(record: unknown): CoverageBin | undefined {
  if (!recordIsObject(record)) return undefined
  const chromosome = asString(record.chromosome)
  const start = asNumber(record.start)
  const end = asNumber(record.end)
  const coverage = asNumber(record.coverage)
  if (chromosome === undefined || chromosome.length === 0) return undefined
  if (start === undefined || end === undefined) return undefined
  if (!Number.isInteger(start) || !Number.isInteger(end)) return undefined
  if (coverage === undefined || !Number.isFinite(coverage)) return undefined
  return {
    chromosome,
    start,
    end,
    coverage,
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  }
}

/** Builds a normalized `CoverageDataset` from raw records. */
export function coverageFromRecords(record: unknown): CoverageDataset | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const title = asString(record.title) ?? 'Coverage'
  const rawBins = Array.isArray(record.bins) ? record.bins : []
  const bins = rawBins.map(toCoverageBin).filter((bin): bin is CoverageBin => bin !== undefined)
  return normalizeCoverageDataset({
    id,
    title,
    bins,
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  })
}

export interface RawDistributionRecord {
  id?: unknown
  title?: unknown
  values?: unknown
  metadata?: unknown
  [key: string]: unknown
}

export interface RawDistributionValueRecord {
  group?: unknown
  value?: unknown
  metadata?: unknown
  [key: string]: unknown
}

/** Normalizes a raw distribution value record, or `undefined` when invalid. */
export function toDistributionValue(record: unknown): DistributionValue | undefined {
  if (!recordIsObject(record)) return undefined
  const group = asString(record.group)
  const value = asNumber(record.value)
  if (group === undefined || group.length === 0) return undefined
  if (value === undefined || !Number.isFinite(value)) return undefined
  return {
    group,
    value,
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  }
}

/** Builds a normalized `DistributionDataset` from raw records. */
export function distributionFromRecords(record: unknown): DistributionDataset | undefined {
  if (!recordIsObject(record)) return undefined
  const id = asString(record.id)
  if (id === undefined || id.length === 0) return undefined
  const title = asString(record.title) ?? 'Distribution'
  const rawValues = Array.isArray(record.values) ? record.values : []
  const values = rawValues
    .map(toDistributionValue)
    .filter((value): value is DistributionValue => value !== undefined)
  return normalizeDistributionDataset({
    id,
    title,
    values,
    ...(optionalMetadata(record) !== undefined ? { metadata: optionalMetadata(record) } : {}),
  })
}

async function fetchDatasetRecord(
  path: string,
  datasetId: string,
  kind: string,
  signal?: AbortSignal,
): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}${path}${encodeURIComponent(datasetId)}`, {
    headers: { 'Content-Type': 'application/json' },
    signal,
  })
  if (!response.ok) {
    throw new GenomeApiError(
      `GenomeAI API returned ${response.status} for ${kind} dataset ${datasetId}`,
      response.status,
    )
  }
  try {
    return await response.json()
  } catch (cause) {
    if (
      typeof cause === 'object' &&
      cause !== null &&
      'name' in cause &&
      (cause as { name?: unknown }).name === 'AbortError'
    ) {
      throw cause
    }
    throw new GenomeApiError(
      `GenomeAI API returned an unreadable response for ${kind} dataset ${datasetId}`,
    )
  }
}

function requireDataset<T>(dataset: T | undefined, kind: string, datasetId: string): T {
  if (dataset === undefined) {
    throw new GenomeApiError(
      `GenomeAI API returned an invalid payload for ${kind} dataset ${datasetId}`,
    )
  }
  return dataset
}

/**
 * Fetches a heatmap dataset from the (not-yet-existing) advanced endpoints.
 * Throws `GenomeApiError` on failure today so the limitation is explicit and
 * typed. Fixture-based demos bypass these loaders.
 */
export async function fetchHeatmapDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<HeatmapDataset> {
  const payload = await fetchDatasetRecord('/advanced/heatmaps/', datasetId, 'heatmap', signal)
  return requireDataset(heatmapFromRecords(payload), 'heatmap', datasetId)
}

export async function fetchVolcanoDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<VolcanoDataset> {
  const payload = await fetchDatasetRecord('/advanced/volcano/', datasetId, 'volcano', signal)
  return requireDataset(volcanoFromRecords(payload), 'volcano', datasetId)
}

export async function fetchCoverageDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<CoverageDataset> {
  const payload = await fetchDatasetRecord('/advanced/coverage/', datasetId, 'coverage', signal)
  return requireDataset(coverageFromRecords(payload), 'coverage', datasetId)
}

export async function fetchDistributionDataset(
  datasetId: string,
  signal?: AbortSignal,
): Promise<DistributionDataset> {
  const payload = await fetchDatasetRecord(
    '/advanced/distributions/',
    datasetId,
    'distribution',
    signal,
  )
  return requireDataset(distributionFromRecords(payload), 'distribution', datasetId)
}
