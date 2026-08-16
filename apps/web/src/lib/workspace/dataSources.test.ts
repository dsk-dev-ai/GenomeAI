import { describe, expect, it } from 'vitest'

import { resolveFixture } from './dataSources'

describe('resolveFixture', () => {
  it('resolves the fixture value as-is', async () => {
    const value = { id: 'dataset-1', title: 'Fixture' }
    await expect(resolveFixture(value)(new AbortController().signal)).resolves.toBe(value)
  })

  it('rejects with an AbortError when the signal is already aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(resolveFixture({})(controller.signal)).rejects.toMatchObject({
      name: 'AbortError',
    })
  })

  it('resolves a fresh value per call without sharing a cache', async () => {
    const loader = resolveFixture(42)
    await expect(loader(new AbortController().signal)).resolves.toBe(42)
    await expect(loader(new AbortController().signal)).resolves.toBe(42)
  })
})
