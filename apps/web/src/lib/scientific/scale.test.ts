import { describe, expect, it } from 'vitest'

import {
  categoryLabelTicks,
  continuousNiceTickStep,
  createCategoryScale,
  createContinuousScale,
  formatTickValue,
  niceTicks,
} from './scale'

describe('createContinuousScale', () => {
  it('maps domain onto a pixel range in both directions', () => {
    const scale = createContinuousScale([0, 100], [0, 500])
    expect(scale.toPixel(0)).toBe(0)
    expect(scale.toPixel(100)).toBe(500)
    expect(scale.toPixel(50)).toBe(250)
    expect(scale.invert(250)).toBe(50)
  })

  it('supports inverted ranges (top-down y-axis)', () => {
    const scale = createContinuousScale([0, 10], [400, 0])
    expect(scale.toPixel(0)).toBe(400)
    expect(scale.toPixel(10)).toBe(0)
  })

  it('handles negative domains', () => {
    const scale = createContinuousScale([-5, 5], [0, 100])
    expect(scale.toPixel(-5)).toBe(0)
    expect(scale.toPixel(5)).toBe(100)
    expect(scale.toPixel(0)).toBe(50)
  })

  it('degenerates safely when the domain or range has zero span', () => {
    const flat = createContinuousScale([7, 7], [0, 100])
    expect(flat.toPixel(7)).toBe(0)
    const flatRange = createContinuousScale([0, 10], [5, 5])
    expect(flatRange.invert(5)).toBe(0)
  })
})

describe('niceTicks and continuousNiceTickStep', () => {
  it('produces ascending human-friendly ticks at 1/2/5 x 10^n steps', () => {
    const ticks = niceTicks(0, 100, 5)
    expect(ticks.length).toBeGreaterThan(0)
    for (let index = 1; index < ticks.length; index += 1) {
      expect(ticks[index]).toBeGreaterThan(ticks[index - 1])
    }
    expect(ticks).toContain(0)
  })

  it('supports negative and fractional domains', () => {
    const ticks = niceTicks(-0.7, 1.2, 6)
    expect(ticks.length).toBeGreaterThan(0)
    for (const tick of ticks) {
      expect(tick).toBeGreaterThanOrEqual(-0.7 - 1e-9)
      expect(tick).toBeLessThanOrEqual(1.2 + 1e-9)
    }
    expect(niceTicks(-3, -1, 5).every((tick) => tick < 0)).toBe(true)
  })

  it('returns degenerate values for empty or flat domains', () => {
    expect(niceTicks(Number.NaN, 1)).toEqual([])
    expect(niceTicks(0, 0)).toEqual([0])
    expect(continuousNiceTickStep(0, 0)).toBe(1)
  })
})

describe('formatTickValue', () => {
  it('trims floating-point noise and uses compact suffixes', () => {
    expect(formatTickValue(0.30000000000000004)).toBe('0.3')
    expect(formatTickValue(1500)).toBe('1.5K')
    expect(formatTickValue(2500000)).toBe('2.50M')
    expect(formatTickValue(-4)).toBe('-4')
  })

  it('returns an empty string for non-finite values', () => {
    expect(formatTickValue(Number.NaN)).toBe('')
  })
})

describe('createCategoryScale', () => {
  it('spaces categories evenly across a range', () => {
    const scale = createCategoryScale(['A', 'B', 'C'], [0, 200])
    expect(scale.toPixel('A')).toBe(0)
    expect(scale.toPixel('B')).toBe(100)
    expect(scale.toPixel('C')).toBe(200)
    expect(scale.step).toBe(100)
    expect(scale.indexOf('B')).toBe(1)
    expect(scale.indexOf('missing')).toBe(-1)
    expect(scale.toPixel('missing')).toBe(0)
  })

  it('centers a single category', () => {
    const scale = createCategoryScale(['A'], [0, 200])
    expect(scale.toPixel('A')).toBe(100)
    expect(scale.slot('A')).toEqual([0, 200])
  })

  it('reports slot extents for multi-category scales', () => {
    const scale = createCategoryScale(['A', 'B', 'C'], [0, 200])
    expect(scale.slot('B')).toEqual([50, 150])
    expect(scale.slot('missing')).toBeUndefined()
  })
})

describe('categoryLabelTicks', () => {
  it('labels every category when they fit', () => {
    const scale = createCategoryScale(['A', 'B', 'C'], [0, 300])
    const ticks = categoryLabelTicks(scale, 300)
    expect(ticks.map((tick) => tick.sample)).toEqual(['A', 'B', 'C'])
    expect(ticks.every((tick) => tick.visible)).toBe(true)
  })

  it('steps labels when they do not fit, deterministically', () => {
    const samples = Array.from({ length: 12 }, (_, index) => `S${index}`)
    const scale = createCategoryScale(samples, [0, 300])
    const ticks = categoryLabelTicks(scale, 300, 36)
    const visible = ticks.filter((tick) => tick.visible)
    expect(visible.length).toBeGreaterThan(0)
    expect(visible.length).toBeLessThan(ticks.length)
    expect(visible[0].sample).toBe('S0')
  })
})
