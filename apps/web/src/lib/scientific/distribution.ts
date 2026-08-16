/**
 * Distribution dataset validation, normalization, grouping, and tooltips
 * (Phase 6.8).
 *
 * Pure functions over `DistributionDataset`. Grouped summary statistics are
 * computed by `lib/scientific/statistics.ts`; this module owns the
 * dataset-shaped concerns:
 *
 * - `validateDistributionDataset` reports invalid values (empty group or
 *   non-finite value).
 * - `normalizeDistributionDataset` builds a deterministic, render-ready
 *   dataset (invalid values dropped, groups ordered canonically, values
 *   within each group sorted ascending).
 * - `distributionGroups` returns the sorted group names.
 * - `groupStatistics` and `groupWhiskers` derive per-group summaries.
 * - `distributionTooltip` maps a group to the labelled tooltip rows.
 */

import type { DistributionDataset, DistributionValue } from './advancedTypes'
import type { SummaryStatistics, Whiskers } from './statistics'
import { boxPlotWhiskers, summarize } from './statistics'
import type { PointTooltip } from './tooltip'
import { formatTooltipValue } from './tooltip'

export interface DistributionValidationResult {
  valid: boolean
  errors: string[]
}

function isValidIdentifier(value: string): boolean {
  return value.trim().length > 0
}

/** Reports problems with a distribution dataset. Empty groups or non-finite
 * values are invalid. */
export function validateDistributionDataset(
  dataset: DistributionDataset,
): DistributionValidationResult {
  const errors: string[] = []
  if (!isValidIdentifier(dataset.id)) {
    errors.push('Dataset id must be a non-empty string.')
  }
  if (!isValidIdentifier(dataset.title)) {
    errors.push('Dataset title must be a non-empty string.')
  }
  dataset.values.forEach((value, index) => {
    if (!isValidIdentifier(value.group)) {
      errors.push(`Value ${index}: group must be a non-empty string.`)
    }
    if (!Number.isFinite(value.value)) {
      errors.push(`Value ${index}: value must be a finite number.`)
    }
  })
  return { valid: errors.length === 0, errors }
}

function compareText(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0
}

function cloneValue(value: DistributionValue): DistributionValue {
  return {
    ...value,
    ...(value.metadata !== undefined ? { metadata: { ...value.metadata } } : {}),
  }
}

/**
 * Builds a deterministic, render-ready distribution dataset: invalid values
 * are dropped, values are ordered by group then ascending value, and groups
 * are canonically ordered on read (via `distributionGroups`). The result
 * never shares mutable state with the input.
 */
export function normalizeDistributionDataset(dataset: DistributionDataset): DistributionDataset {
  const values = dataset.values
    .filter((value) => {
      if (!isValidIdentifier(value.group)) return false
      return Number.isFinite(value.value)
    })
    .map(cloneValue)
    .sort((left, right) => {
      const byGroup = compareText(left.group, right.group)
      if (byGroup !== 0) return byGroup
      return left.value - right.value
    })

  return {
    id: dataset.id.trim().length > 0 ? dataset.id : 'unnamed-distribution',
    title: dataset.title.trim().length > 0 ? dataset.title : 'Unnamed distribution',
    values,
    ...(dataset.metadata !== undefined ? { metadata: { ...dataset.metadata } } : {}),
  }
}

/** Whether the dataset holds at least one renderable value. */
export function hasRenderableValues(dataset: DistributionDataset): boolean {
  return dataset.values.length > 0
}

/**
 * The sorted, unique set of group names. Drives the categorical x-axis;
 * ordering is deterministic (code-unit compare).
 */
export function distributionGroups(dataset: DistributionDataset): string[] {
  const groups = new Set<string>()
  for (const value of dataset.values) {
    if (value.group.trim().length > 0) groups.add(value.group)
  }
  return [...groups].sort(compareText)
}

/**
 * The values belonging to a group, in their stored order. This scans the
 * whole dataset per call; prefer `valuesByGroup` (one pass) when summarizing
 * many groups at once.
 */
export function valuesForGroup(dataset: DistributionDataset, group: string): number[] {
  return dataset.values.filter((value) => value.group === group).map((value) => value.value)
}

/**
 * Groups all dataset values by group name in a single pass, preserving the
 * stored order within each group. Used by the chart hook to derive every
 * group's statistics without re-scanning the dataset per group (O(values)
 * instead of O(groups × values)).
 */
export function valuesByGroup(dataset: DistributionDataset): Map<string, number[]> {
  const grouped = new Map<string, number[]>()
  for (const value of dataset.values) {
    if (value.group.trim().length === 0) continue
    const list = grouped.get(value.group)
    if (list === undefined) {
      grouped.set(value.group, [value.value])
    } else {
      list.push(value.value)
    }
  }
  return grouped
}

/** Summary statistics for a single group, or `undefined` when empty. */
export function groupStatistics(
  dataset: DistributionDataset,
  group: string,
): SummaryStatistics | undefined {
  return summarize(valuesForGroup(dataset, group))
}

/** Box-plot whiskers for a single group, or `undefined` when empty. */
export function groupWhiskers(dataset: DistributionDataset, group: string): Whiskers | undefined {
  return boxPlotWhiskers(valuesForGroup(dataset, group))
}

/**
 * Builds the tooltip content for a group's summary. The title is the group
 * name, the subtitle states the sample size, and the rows carry the key
 * summary statistics.
 */
export function distributionTooltip(dataset: DistributionDataset, group: string): PointTooltip {
  const summary = groupStatistics(dataset, group)
  const whiskers = groupWhiskers(dataset, group)
  const rows = [
    { label: 'Count', value: String(summary?.count ?? 0) },
    { label: 'Mean', value: formatTooltipValue(summary?.mean ?? Number.NaN) },
    { label: 'Median', value: formatTooltipValue(summary?.q2 ?? Number.NaN) },
    { label: 'Min', value: formatTooltipValue(summary?.min ?? Number.NaN) },
    { label: 'Max', value: formatTooltipValue(summary?.max ?? Number.NaN) },
    { label: 'Q1', value: formatTooltipValue(summary?.q1 ?? Number.NaN) },
    { label: 'Q3', value: formatTooltipValue(summary?.q3 ?? Number.NaN) },
    ...(whiskers !== undefined && whiskers.outliers.length > 0
      ? [{ label: 'Outliers', value: String(whiskers.outliers.length) }]
      : []),
  ]
  return {
    title: group,
    subtitle: `${summary?.count ?? 0} values`,
    rows,
  }
}
