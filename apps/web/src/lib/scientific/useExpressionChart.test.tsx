import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_PATHWAY_EXPRESSION_FIXTURE, buildExpressionDataset } from './expression.fixtures'
import { useExpressionChart } from './useExpressionChart'

function Harness({
  onModel,
  options = {},
}: {
  onModel: (model: ReturnType<typeof useExpressionChart>) => void
  options?: Parameters<typeof useExpressionChart>[0]
}) {
  const model = useExpressionChart(options)
  onModel(model)
  return <output data-testid="status">{model.status}</output>
}

/** Renders the hook and exposes its latest result via a safe getter. */
function renderHook(options: Parameters<typeof useExpressionChart>[0] = {}) {
  let model: ReturnType<typeof useExpressionChart> | undefined
  render(
    <Harness
      options={options}
      onModel={(next) => {
        model = next
      }}
    />,
  )
  return {
    get model(): ReturnType<typeof useExpressionChart> {
      if (model === undefined) {
        throw new Error('useExpressionChart did not capture a model (expected after success)')
      }
      return model
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useExpressionChart', () => {
  it('loads a dataset and reports success', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_EXPRESSION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.model.dataset?.id).toBe('expression-tp53-pathway')
  })

  it('reports empty for an empty dataset', async () => {
    const empty = buildExpressionDataset({ series: [] })
    const loader = vi.fn(async () => empty)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.model.dataset).toBeDefined()
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('expression down'))
      .mockResolvedValueOnce(TP53_PATHWAY_EXPRESSION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.model.error?.message).toBe('expression down')

    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('derives sorted samples, the value domain, and normalized availability', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_EXPRESSION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.model.samples).toEqual([
      'Normal-1',
      'Normal-2',
      'Normal-3',
      'Tumor-1',
      'Tumor-2',
      'Tumor-3',
    ])
    expect(captured.model.hasNormalizedValues).toBe(true)
    expect(captured.model.valueField).toBe('value')
    expect(captured.model.valueDomain.min).toBeGreaterThanOrEqual(0)
  })

  it('switches the value field and updates the domain', async () => {
    const loader = vi.fn(async () => TP53_PATHWAY_EXPRESSION_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))

    captured.model.setValueField('normalizedValue')
    await waitFor(() => expect(captured.model.valueField).toBe('normalizedValue'))
    expect(captured.model.valueDomain.min).toBeLessThan(0)
    expect(captured.model.valueDomain.max).toBeGreaterThan(0)
  })

  it('falls back to raw values when no normalized values exist', async () => {
    const rawOnly = buildExpressionDataset({
      series: [{ id: 's1', label: 'S1', points: [['Tumor-1', 5]] }],
    })
    const loader = vi.fn(async () => rawOnly)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.model.hasNormalizedValues).toBe(false)

    captured.model.setValueField('normalizedValue')
    await waitFor(() => expect(captured.model.valueField).toBe('value'))
  })

  it('tracks point selection and clears it when a new dataset loads', async () => {
    let current = TP53_PATHWAY_EXPRESSION_FIXTURE
    const loader = vi.fn(async () => current)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))

    captured.model.selectPoint('tp53:TP53@Tumor-1')
    await waitFor(() => expect(captured.model.selectedKey).toBe('tp53:TP53@Tumor-1'))

    current = { ...buildExpressionDataset({ series: [] }), id: 'expression-other' }
    captured.model.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    await waitFor(() => expect(captured.model.selectedKey).toBeNull())
  })

  it('loads through the default fetchExpressionDataset loader when only datasetId is given', async () => {
    const captured = renderHook({ datasetId: 'expression-tp53-pathway' })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    // No backend during tests: fetch rejects, which is the expected lifecycle.
    expect(captured.model.error).toBeDefined()
  })
})
