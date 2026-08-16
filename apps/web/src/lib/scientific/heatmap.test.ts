import { describe, expect, it } from 'vitest'

import type { HeatmapDataset } from './advancedTypes'
import {
  hasRenderableValues,
  heatmapCellKey,
  heatmapCellTooltip,
  heatmapColorScale,
  heatmapValueDomain,
  normalizeHeatmapDataset,
  parseHeatmapCellKey,
  validateHeatmapDataset,
} from './heatmap'

function matrix(
  values: Array<Array<number | undefined>>,
  overrides: Partial<HeatmapDataset> = {},
): HeatmapDataset {
  return {
    id: 'heatmap-test',
    title: 'Test heatmap',
    rows: overrides.rows ?? ['row-1', 'row-2'],
    columns: overrides.columns ?? ['col-1', 'col-2'],
    values,
    ...overrides,
  }
}

describe('validateHeatmapDataset', () => {
  it('accepts a rectangular finite matrix', () => {
    const result = validateHeatmapDataset(
      matrix([
        [1, 2],
        [3, 4],
      ]),
    )
    expect(result.valid).toBe(true)
    expect(result.errors).toEqual([])
  })

  it('accepts undefined (missing) values', () => {
    const result = validateHeatmapDataset(
      matrix([
        [1, undefined],
        [3, 4],
      ]),
    )
    expect(result.valid).toBe(true)
  })

  it('rejects a ragged matrix', () => {
    const result = validateHeatmapDataset(matrix([[1, 2], [3]]))
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/1 values/)
  })

  it('rejects non-finite values', () => {
    const result = validateHeatmapDataset(
      matrix([
        [1, Number.NaN],
        [3, 4],
      ]),
    )
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/finite/)
  })

  it('rejects duplicate row and column identifiers', () => {
    const result = validateHeatmapDataset(
      matrix(
        [
          [1, 2],
          [3, 4],
        ],
        { rows: ['a', 'a'], columns: ['b', 'b'] },
      ),
    )
    expect(result.valid).toBe(false)
    expect(result.errors.join(' ')).toMatch(/Duplicate row/)
    expect(result.errors.join(' ')).toMatch(/Duplicate column/)
  })

  it('rejects empty identifiers and titles', () => {
    const result = validateHeatmapDataset(
      matrix(
        [
          [1, 2],
          [3, 4],
        ],
        { id: '', title: '' },
      ),
    )
    expect(result.valid).toBe(false)
  })
})

describe('normalizeHeatmapDataset', () => {
  it('sorts rows and columns canonically and re-arranges the matrix', () => {
    const normalized = normalizeHeatmapDataset(
      matrix(
        [
          [1, 2],
          [3, 4],
        ],
        { rows: ['z', 'a'], columns: ['y', 'b'] },
      ),
    )
    expect(normalized.rows).toEqual(['a', 'z'])
    expect(normalized.columns).toEqual(['b', 'y'])
    // Original matrix: rows z=[1,2], a=[3,4]; columns y, b.
    // Normalized rows a=[3,4], z=[1,2]; columns b, y => a: [4,3], z: [2,1].
    expect(normalized.values).toEqual([
      [4, 3],
      [2, 1],
    ])
  })

  it('dedupes duplicate axis identifiers, keeping the first', () => {
    const normalized = normalizeHeatmapDataset(
      matrix(
        [
          [1, 2],
          [3, 4],
        ],
        { rows: ['a', 'a'], columns: ['b', 'b'] },
      ),
    )
    expect(normalized.rows).toEqual(['a'])
    expect(normalized.columns).toEqual(['b'])
  })

  it('converts non-finite values to undefined instead of dropping rows', () => {
    const normalized = normalizeHeatmapDataset(
      matrix([
        [Number.NaN, 2],
        [3, 4],
      ]),
    )
    expect(normalized.values[0][0]).toBeUndefined()
    expect(normalized.values[0][1]).toBe(2)
  })

  it('never mutates the input', () => {
    const input = matrix([
      [1, 2],
      [3, 4],
    ])
    normalizeHeatmapDataset(input)
    expect(input.rows).toEqual(['row-1', 'row-2'])
    expect(input.columns).toEqual(['col-1', 'col-2'])
    expect(input.values).toEqual([
      [1, 2],
      [3, 4],
    ])
  })
})

describe('hasRenderableValues', () => {
  it('is false when every value is undefined', () => {
    expect(
      hasRenderableValues(
        matrix([
          [undefined, undefined],
          [undefined, undefined],
        ]),
      ),
    ).toBe(false)
  })

  it('is true when at least one value is finite', () => {
    expect(
      hasRenderableValues(
        matrix([
          [undefined, 1],
          [undefined, undefined],
        ]),
      ),
    ).toBe(true)
  })
})

describe('heatmapValueDomain', () => {
  it('returns the min/max over finite values', () => {
    expect(
      heatmapValueDomain(
        matrix([
          [1, 2],
          [3, 4],
        ]),
      ),
    ).toEqual({ min: 1, max: 4 })
  })

  it('ignores undefined values', () => {
    expect(
      heatmapValueDomain(
        matrix([
          [undefined, 5],
          [undefined, undefined],
        ]),
      ),
    ).toEqual({ min: 5, max: 5 })
  })

  it('returns undefined when no finite value exists', () => {
    expect(
      heatmapValueDomain(
        matrix([
          [undefined, undefined],
          [undefined, undefined],
        ]),
      ),
    ).toBeUndefined()
  })
})

describe('heatmapColorScale', () => {
  it('maps domain.min to the low color', () => {
    const scale = heatmapColorScale({ min: -1, max: 1 })
    expect(scale(-1)).toBe('rgb(29, 78, 216)')
  })

  it('maps the center to the midpoint', () => {
    const scale = heatmapColorScale({ min: -1, max: 1 })
    expect(scale(0)).toBe('rgb(248, 250, 252)')
  })

  it('maps domain.max to the high color', () => {
    const scale = heatmapColorScale({ min: -1, max: 1 })
    expect(scale(1)).toBe('rgb(185, 28, 28)')
  })

  it('clamps values outside the domain', () => {
    const scale = heatmapColorScale({ min: -1, max: 1 })
    expect(scale(100)).toBe('rgb(185, 28, 28)')
    expect(scale(-100)).toBe('rgb(29, 78, 216)')
  })

  it('supports a custom center', () => {
    const scale = heatmapColorScale({ min: 0, max: 10 }, { center: 5 })
    expect(scale(5)).toBe('rgb(248, 250, 252)')
    expect(scale(0)).toBe('rgb(29, 78, 216)')
    expect(scale(10)).toBe('rgb(185, 28, 28)')
  })
})

describe('heatmapCellKey / parseHeatmapCellKey', () => {
  it('round-trips a cell key', () => {
    const key = heatmapCellKey({ row: 'gene:1', column: 'sample@2' })
    expect(parseHeatmapCellKey(key)).toEqual({ row: 'gene:1', column: 'sample@2' })
  })

  it('is collision-free for length-prefixed fields', () => {
    const a = heatmapCellKey({ row: 'ab', column: 'c' })
    const b = heatmapCellKey({ row: 'a', column: 'bc' })
    expect(a).not.toBe(b)
  })

  it('returns undefined for a malformed key', () => {
    expect(parseHeatmapCellKey('not-a-key')).toBeUndefined()
  })
})

describe('heatmapCellTooltip', () => {
  it('renders a finite value', () => {
    const tooltip = heatmapCellTooltip(
      matrix(
        [
          [1, 2],
          [3, 4],
        ],
        { rowLabels: { 'row-1': 'Gene A' } },
      ),
      'row-1',
      'col-1',
      1,
    )
    expect(tooltip.title).toBe('Gene A')
    expect(tooltip.subtitle).toBe('col-1')
    expect(tooltip.rows[0]).toEqual({ label: 'Value', value: '1' })
  })

  it('marks missing values distinctly', () => {
    const tooltip = heatmapCellTooltip(
      matrix([
        [1, 2],
        [3, 4],
      ]),
      'row-1',
      'col-1',
      undefined,
    )
    expect(tooltip.rows[0]).toEqual({ label: 'Value', value: 'missing' })
  })

  it('falls back to the raw identifier for labels', () => {
    const tooltip = heatmapCellTooltip(
      matrix([
        [1, 2],
        [3, 4],
      ]),
      'row-1',
      'col-1',
      1,
    )
    expect(tooltip.title).toBe('row-1')
  })
})
