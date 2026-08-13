import { describe, expect, it } from 'vitest'

import { formatTooltipValue, lookupPoint, pointTooltip } from './tooltip'
import type { ExpressionDataset } from './types'

function dataset(): ExpressionDataset {
  return {
    id: 'd',
    title: 'Dataset',
    series: [
      {
        id: 'tp53',
        label: 'TP53',
        points: [
          {
            identifier: 'TP53',
            sample: 'Tumor-1',
            value: 128.4,
            normalizedValue: 1.92,
            metadata: { status: 'overexpressed' },
          },
          { identifier: 'TP53', sample: 'Normal-1', value: 44.2 },
        ],
      },
    ],
  }
}

describe('formatTooltipValue', () => {
  it('trims floating-point noise and handles non-finite values', () => {
    expect(formatTooltipValue(128.39999999999998)).toBe('128.4')
    expect(formatTooltipValue(0)).toBe('0')
    expect(formatTooltipValue(Number.NaN)).toBe('\u2013')
  })
})

describe('pointTooltip', () => {
  it('maps a point to title, subtitle, and rows', () => {
    const data = dataset()
    const series = data.series[0]
    const tooltip = pointTooltip(series, series.points[0])
    expect(tooltip.title).toBe('TP53')
    expect(tooltip.subtitle).toBe('TP53 — Tumor-1')
    expect(tooltip.rows).toEqual([
      { label: 'Sample', value: 'Tumor-1' },
      { label: 'Value', value: '128.4' },
      { label: 'Normalized', value: '1.92' },
      { label: 'status', value: 'overexpressed' },
    ])
  })

  it('omits normalized and metadata rows when absent', () => {
    const data = dataset()
    const series = data.series[0]
    const tooltip = pointTooltip(series, series.points[1])
    expect(tooltip.rows.map((row) => row.label)).toEqual(['Sample', 'Value'])
  })
})

describe('lookupPoint', () => {
  it('finds a point by its series, identifier, and sample', () => {
    const data = dataset()
    const lookup = lookupPoint(data, { seriesId: 'tp53', pointId: 'TP53', sample: 'Tumor-1' })
    expect(lookup?.series.id).toBe('tp53')
    expect(lookup?.point.sample).toBe('Tumor-1')
  })

  it('resolves the correct point when identifiers repeat across samples', () => {
    const data = dataset()
    const lookup = lookupPoint(data, { seriesId: 'tp53', pointId: 'TP53', sample: 'Normal-1' })
    expect(lookup?.point.value).toBe(44.2)
  })

  it('returns undefined for unknown series, points, or samples', () => {
    const data = dataset()
    expect(
      lookupPoint(data, { seriesId: 'missing', pointId: 'TP53', sample: 'Tumor-1' }),
    ).toBeUndefined()
    expect(
      lookupPoint(data, { seriesId: 'tp53', pointId: 'missing', sample: 'Tumor-1' }),
    ).toBeUndefined()
    expect(
      lookupPoint(data, { seriesId: 'tp53', pointId: 'TP53', sample: 'Missing' }),
    ).toBeUndefined()
  })
})
