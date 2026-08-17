import { describe, expect, it, vi } from 'vitest'

import { abortAware, resolveFixture } from './dataSources'

describe('abortAware', () => {
  it('runs the resolver when the signal is not aborted', async () => {
    const resolver = vi.fn(() => Promise.resolve('ok'))
    await expect(abortAware(resolver)(new AbortController().signal)).resolves.toBe('ok')
    expect(resolver).toHaveBeenCalledTimes(1)
  })

  it('rejects with an AbortError without running the resolver when already aborted', async () => {
    const resolver = vi.fn(() => Promise.resolve('ok'))
    const controller = new AbortController()
    controller.abort()
    await expect(abortAware(resolver)(controller.signal)).rejects.toMatchObject({
      name: 'AbortError',
    })
    expect(resolver).not.toHaveBeenCalled()
  })
})

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
