import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchVisualizationModules } from './visualizationModules'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('fetchVisualizationModules', () => {
  it('resolves the demo catalog with every delivered module', async () => {
    const modules = await fetchVisualizationModules(new AbortController().signal, { delayMs: 0 })

    expect(modules.map((module) => module.id)).toEqual([
      'genome-browser',
      'gene-transcript-viewer',
      'variant-viewer',
      'protein-viewer',
      'network-viewer',
      'scientific-charts',
      'advanced-scientific-charts',
      'integrated-research-workspace',
      'performance-large-datasets',
      'testing-documentation',
      'molecular-structure-viewer',
    ])
    for (const module of modules) {
      expect(module.title).toBeTruthy()
      expect(module.milestone).toMatch(/^6\.\d+$/)
      expect(module.source.kind).toBe('api')
    }
  })

  it('returns a fresh copy of the catalog, not the internal array', async () => {
    const signal = new AbortController().signal
    const first = await fetchVisualizationModules(signal, { delayMs: 0 })
    const second = await fetchVisualizationModules(signal, { delayMs: 0 })
    expect(first).not.toBe(second)
    first.pop()
    expect((await fetchVisualizationModules(signal, { delayMs: 0 })).length).toBe(11)
  })

  it('honours the simulated latency before resolving', async () => {
    vi.useFakeTimers()
    const signal = new AbortController().signal
    const promise = fetchVisualizationModules(signal, { delayMs: 250 })
    const spy = vi.fn()
    promise.then(spy)

    await vi.advanceTimersByTimeAsync(200)
    expect(spy).not.toHaveBeenCalled()

    await vi.advanceTimersByTimeAsync(50)
    expect(spy).toHaveBeenCalledTimes(1)
    vi.useRealTimers()
  })

  it('rejects with the configured failure message', async () => {
    const signal = new AbortController().signal
    await expect(
      fetchVisualizationModules(signal, { delayMs: 0, failWith: 'catalog down' }),
    ).rejects.toThrow('catalog down')
  })

  it('rejects with an AbortError when the signal is already aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(
      fetchVisualizationModules(controller.signal, { delayMs: 0 }),
    ).rejects.toMatchObject({ name: 'AbortError' })
  })

  it('rejects with an AbortError and stops the timer when aborted while pending', async () => {
    vi.useFakeTimers()
    const controller = new AbortController()
    const promise = fetchVisualizationModules(controller.signal, { delayMs: 1000 })
    const assertion = expect(promise).rejects.toMatchObject({ name: 'AbortError' })

    controller.abort()
    await vi.runAllTimersAsync()

    await assertion
    vi.useRealTimers()
  })
})
