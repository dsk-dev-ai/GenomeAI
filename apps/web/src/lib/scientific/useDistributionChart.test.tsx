import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EXPRESSION_DISTRIBUTION_FIXTURE } from './advanced.fixtures'
import { useDistributionChart } from './useDistributionChart'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useDistributionChart>) => void
  options?: Parameters<typeof useDistributionChart>[0]
}) {
  const model = useDistributionChart(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

function renderHook(options: Parameters<typeof useDistributionChart>[0] = {}) {
  let model: ReturnType<typeof useDistributionChart> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useDistributionChart> {
      if (model === undefined) {
        throw new Error('useDistributionChart did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useDistributionChart', () => {
  it('loads a dataset, derives groups, and reports success', async () => {
    const loader = vi.fn(async () => EXPRESSION_DISTRIBUTION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.dataset?.id).toBe('distribution-expression-by-condition')
    expect(captured.model.groups).toEqual(['Normal', 'Tumor'])
    expect(captured.model.statistics).toHaveLength(2)
  })

  it('reports empty for an empty dataset', async () => {
    const empty = { id: 'empty', title: 'Empty', values: [] }
    const loader = vi.fn(async () => empty)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.model.groups).toEqual([])
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('distribution down'))
      .mockResolvedValueOnce(EXPRESSION_DISTRIBUTION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('distribution down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('derives per-group statistics and a padded value domain', async () => {
    const loader = vi.fn(async () => EXPRESSION_DISTRIBUTION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    const tumor = captured.model.statistics.find((entry) => entry.group === 'Tumor')
    expect(tumor?.summary?.count).toBe(8)
    expect(captured.model.valueDomain.min).toBeLessThan(captured.model.valueDomain.max)
  })
})
