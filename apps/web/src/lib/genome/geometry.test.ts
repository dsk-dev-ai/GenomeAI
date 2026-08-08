import { describe, expect, it } from 'vitest'

import {
  computeTicks,
  createScale,
  formatBasePosition,
  formatRegionLabel,
  niceTickStep,
} from './geometry'

describe('createScale', () => {
  it('maps the viewport start to x=0 and computes px per base', () => {
    const scale = createScale(1, 100, 200)
    expect(scale.pxPerBase).toBeCloseTo(2)
    expect(scale.toX(1)).toBe(0)
    expect(scale.toX(100)).toBeCloseTo(198)
  })

  it('maps a one-based inclusive span to pixels', () => {
    const scale = createScale(1, 100, 200)
    expect(scale.spanToPixels(51)).toBeCloseTo(102)
  })

  it('handles a zero-length window by using at least one base', () => {
    const scale = createScale(5, 5, 50)
    expect(scale.pxPerBase).toBe(50)
  })
})

describe('niceTickStep', () => {
  it('returns nice 1/2/5 steps', () => {
    expect(niceTickStep(100, 1)).toBe(100)
    expect(niceTickStep(200, 1)).toBe(200)
    expect(niceTickStep(500, 1)).toBe(500)
    expect(niceTickStep(700, 1)).toBe(1000)
  })

  it('honours the minimum step', () => {
    expect(niceTickStep(1, 100)).toBe(100)
  })
})

describe('computeTicks', () => {
  it('produces major labelled ticks inside the interval', () => {
    const ticks = computeTicks(1, 100_000, 10, 4)
    const majors = ticks.filter((tick) => tick.major)
    expect(majors.length).toBeGreaterThan(1)
    expect(majors[0].label).toBeTruthy()
    expect(majors[0].position).toBeGreaterThanOrEqual(1)
    expect(majors[majors.length - 1].position).toBeLessThanOrEqual(100_000)
  })

  it('sorts ticks by position', () => {
    const ticks = computeTicks(1, 1000, 10, 4)
    for (let i = 1; i < ticks.length; i += 1) {
      expect(ticks[i].position).toBeGreaterThan(ticks[i - 1].position)
    }
  })
})

describe('formatBasePosition', () => {
  it('formats millions', () => {
    expect(formatBasePosition(1_240_000)).toBe('1.24M')
    expect(formatBasePosition(2_000_000)).toBe('2M')
  })

  it('formats thousands', () => {
    expect(formatBasePosition(15_000)).toBe('15K')
    expect(formatBasePosition(123_500)).toBe('123.5K')
  })

  it('leaves small positions verbatim', () => {
    expect(formatBasePosition(230)).toBe('230')
  })
})

describe('formatRegionLabel', () => {
  it('formats a grouped region label', () => {
    expect(formatRegionLabel('chr1', 124_500_000, 125_000_000)).toBe('chr1:124,500,000-125,000,000')
  })
})
