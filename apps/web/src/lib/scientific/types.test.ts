import { describe, expect, it } from 'vitest'

import { parsePointKey, pointKeyToString } from './types'
import type { PointKey } from './types'

describe('pointKeyToString / parsePointKey', () => {
  it('round-trips a plain key', () => {
    const key: PointKey = { seriesId: 'tp53', pointId: 'TP53', sample: 'Tumor-1' }
    expect(parsePointKey(pointKeyToString(key))).toEqual(key)
  })

  it('handles delimiters inside the fields', () => {
    const key: PointKey = { seriesId: 'a:b', pointId: 'c@d', sample: 'e:f@g' }
    expect(parsePointKey(pointKeyToString(key))).toEqual(key)
  })

  it('round-trips empty values', () => {
    const key: PointKey = { seriesId: '', pointId: '', sample: '' }
    expect(parsePointKey(pointKeyToString(key))).toEqual(key)
  })

  it('distinguishes keys that collide under a naive encoding', () => {
    const first: PointKey = { seriesId: 'a:b', pointId: 'c', sample: 'd' }
    const second: PointKey = { seriesId: 'a', pointId: 'b:c', sample: 'd' }
    expect(pointKeyToString(first)).not.toBe(pointKeyToString(second))
    expect(parsePointKey(pointKeyToString(first))).toEqual(first)
    expect(parsePointKey(pointKeyToString(second))).toEqual(second)
  })

  it('returns undefined for malformed input', () => {
    expect(parsePointKey('')).toBeUndefined()
    expect(parsePointKey('not-a-key')).toBeUndefined()
    expect(parsePointKey(':')).toBeUndefined()
    expect(parsePointKey('4:tp53')).toBeUndefined()
    expect(parsePointKey('4:tp534:TP537:Tumor-1-extra')).toBeUndefined()
  })
})
