import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_PATHWAY_EXPRESSION_FIXTURE, buildExpressionDataset } from './expression.fixtures'
import { pointKeyToString } from './types'
import { useExpressionChart } from './useExpressionChart'

const TP53_TUMOR_1_KEY = pointKeyToString({ seriesId: 'tp53', pointId: 'TP53', sample: 'Tumor-1' })

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

    captured.model.selectPoint(TP53_TUMOR_1_KEY)
    await waitFor(() => expect(captured.model.selectedKey).toBe(TP53_TUMOR_1_KEY))

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

  it('reloads when the datasetId changes', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith('d1')) {
        return {
          ok: true,
          status: 200,
          json: () =>
            Promise.resolve({
              id: 'd1',
              title: 'Dataset 1',
              series: [
                {
                  id: 's1',
                  label: 'S1',
                  points: [{ identifier: 'A', sample: 'Tumor-1', value: 1 }],
                },
              ],
            }),
        } as unknown as Response
      }
      return {
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            id: 'd2',
            title: 'Dataset 2',
            series: [
              { id: 's2', label: 'S2', points: [{ identifier: 'B', sample: 'Tumor-2', value: 2 }] },
            ],
          }),
      } as unknown as Response
    })
    globalThis.fetch = fetchMock as unknown as typeof fetch

    let model: ReturnType<typeof useExpressionChart> | undefined
    const { rerender } = render(
      <Harness
        options={{ datasetId: 'd1' }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(model?.dataset?.id).toBe('d1')

    rerender(
      <Harness
        options={{ datasetId: 'd2' }}
        onModel={(next) => {
          model = next
        }}
      />,
    )
    await waitFor(() => expect(model?.dataset?.id).toBe('d2'))
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
