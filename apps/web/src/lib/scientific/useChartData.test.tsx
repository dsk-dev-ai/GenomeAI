import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useChartData } from './useChartData'

interface Item {
  id: string
}

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useChartData<Item>>) => void
  options?: Parameters<typeof useChartData<Item>>[0]
}) {
  const model = useChartData<Item>(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

function renderHook(options: Parameters<typeof useChartData<Item>>[0] = {}) {
  let model: ReturnType<typeof useChartData<Item>> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useChartData<Item>> {
      if (model === undefined) {
        throw new Error('useChartData did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useChartData', () => {
  it('loads through a custom loader and reports success', async () => {
    const loader = vi.fn(async () => ({ id: 'a' }))
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.data?.id).toBe('a')
    expect(captured.model.error).toBeUndefined()
  })

  it('reports empty when the isEmpty predicate matches', async () => {
    const loader = vi.fn(async () => ({ id: 'a' }))
    const captured = renderHook({ loader, isEmpty: () => true })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.model.data?.id).toBe('a')
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('down'))
      .mockResolvedValueOnce({ id: 'a' })
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('reports an error when no loader is available', async () => {
    const captured = renderHook({ noLoaderMessage: 'nothing to load' })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('nothing to load')
  })

  it('loads through the defaultLoader when no custom loader is given', async () => {
    const defaultLoader = vi.fn(async (id: string) => ({ id }))
    const captured = renderHook({ datasetId: 'd1', defaultLoader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(defaultLoader).toHaveBeenCalledTimes(1)
    expect(defaultLoader).toHaveBeenCalledWith('d1', expect.any(AbortSignal))
    expect(captured.model.data?.id).toBe('d1')
  })

  it('reloads when the datasetId changes', async () => {
    const defaultLoader = vi.fn(async (id: string) => ({ id }))
    let model: ReturnType<typeof useChartData<Item>> | undefined
    const { rerender } = render(
      <Harness
        options={{ datasetId: 'd1', defaultLoader }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(model?.data?.id).toBe('d1')
    expect(defaultLoader).toHaveBeenCalledTimes(1)

    rerender(
      <Harness
        options={{ datasetId: 'd2', defaultLoader }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(model?.data?.id).toBe('d2'))
    expect(defaultLoader).toHaveBeenCalledTimes(2)
  })

  it('does not reload when the datasetId stays the same', async () => {
    const defaultLoader = vi.fn(async (id: string) => ({ id }))
    let model: ReturnType<typeof useChartData<Item>> | undefined
    const { rerender } = render(
      <Harness
        options={{ datasetId: 'd1', defaultLoader }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))

    rerender(
      <Harness
        options={{ datasetId: 'd1', defaultLoader }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(model?.data?.id).toBe('d1'))
    expect(defaultLoader).toHaveBeenCalledTimes(1)
  })
})
