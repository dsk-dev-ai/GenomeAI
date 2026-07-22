import { describe, expect, it } from 'vitest'
import { VERSION } from './index'

describe('sdk-ts', () => {
  it('exports a version string', () => {
    expect(typeof VERSION).toBe('string')
    expect(VERSION).toBe('0.1.0')
  })
})
