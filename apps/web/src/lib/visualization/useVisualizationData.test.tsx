import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { type VisualizationLoader, useVisualizationData } from './useVisualizationData'

interface Deferred<T> {
  promise: Promise<T>
  resolve: (value: T) => void
  reject: (reason: unknown) => void
}

function deferred<T>(): Deferred<T> {
  let resolveValue!: (value: T) => void
  let rejectValue!: (reason: unknown) => void
  const promise = new Promise<T>((resolve, reject) => {
    resolveValue = resolve
    rejectValue = reject
  })
  return { promise, resolve: resolveValue, reject: rejectValue }
}

function Harness<T>({
  loader,
  isEmpty,
}: {
  loader: VisualizationLoader<T>
  isEmpty?: (data: T) => boolean
}) {
  const { status, data, error, refetch } = useVisualizationData<T>(
    loader,
    isEmpty ? { isEmpty } : {},
  )
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="data">{data === undefined ? '' : JSON.stringify(data)}</div>
      <div data-testid="error">{error?.message ?? ''}</div>
      <button type="button" onClick={refetch}>
        refetch
      </button>
    </div>
  )
}

const statusText = () => screen.getByTestId('status').textContent

afterEach(() => {
  cleanup()
})

describe('useVisualizationData', () => {
  it('resolves to success with the loaded data', async () => {
    render(<Harness loader={() => Promise.resolve(['a', 'b'])} />)

    await waitFor(() => expect(statusText()).toBe('success'))
    expect(screen.getByTestId('data').textContent).toBe('["a","b"]')
    expect(screen.getByTestId('error').textContent).toBe('')
  })

  it('shows loading while the request is pending', async () => {
    const pending = deferred<string>()
    render(<Harness loader={() => pending.promise} />)

    expect(statusText()).toBe('loading')

    await act(async () => {
      pending.resolve('done')
    })
    expect(statusText()).toBe('success')
    expect(screen.getByTestId('data').textContent).toBe('"done"')
  })

  it('resolves to error and surfaces the error message', async () => {
    render(<Harness loader={() => Promise.reject(new Error('boom'))} />)

    await waitFor(() => expect(statusText()).toBe('error'))
    expect(screen.getByTestId('error').textContent).toBe('boom')
  })

  it('resolves to empty when the isEmpty predicate matches', async () => {
    render(<Harness loader={() => Promise.resolve([])} isEmpty={(data) => data.length === 0} />)

    await waitFor(() => expect(statusText()).toBe('empty'))
  })

  it('ignores stale responses when a newer request supersedes an in-flight one', async () => {
    const first = deferred<string>()
    const second = deferred<string>()
    let callCount = 0
    const loader = () => (callCount++ === 0 ? first.promise : second.promise)

    render(<Harness loader={loader} />)
    await waitFor(() => expect(statusText()).toBe('loading'))

    fireEvent.click(screen.getByRole('button', { name: 'refetch' }))

    await act(async () => {
      second.resolve('second')
    })
    expect(statusText()).toBe('success')
    expect(screen.getByTestId('data').textContent).toBe('"second"')

    await act(async () => {
      first.resolve('first')
    })
    expect(screen.getByTestId('data').textContent).toBe('"second"')
  })

  it('does not surface an error when the request is aborted', async () => {
    render(<Harness loader={() => Promise.reject(new DOMException('aborted', 'AbortError'))} />)

    await waitFor(() => expect(statusText()).toBe('loading'))
    expect(screen.getByTestId('error').textContent).toBe('')
  })

  it('aborts the in-flight request when the consumer unmounts', async () => {
    let capturedSignal: AbortSignal | undefined
    const loader = (signal: AbortSignal) => {
      capturedSignal = signal
      return new Promise<string>(() => undefined)
    }

    const { unmount } = render(<Harness loader={loader} />)
    await waitFor(() => expect(capturedSignal).toBeDefined())
    expect(capturedSignal?.aborted).toBe(false)

    unmount()
    expect(capturedSignal?.aborted).toBe(true)
  })

  it('refetch re-runs the loader and replaces the error state', async () => {
    let shouldFail = true
    const loader = () =>
      shouldFail ? Promise.reject(new Error('first failure')) : Promise.resolve('recovered')

    render(<Harness loader={loader} />)
    await waitFor(() => expect(statusText()).toBe('error'))
    expect(screen.getByTestId('error').textContent).toBe('first failure')

    shouldFail = false
    fireEvent.click(screen.getByRole('button', { name: 'refetch' }))
    await waitFor(() => expect(statusText()).toBe('success'))
    expect(screen.getByTestId('data').textContent).toBe('"recovered"')
  })
})
