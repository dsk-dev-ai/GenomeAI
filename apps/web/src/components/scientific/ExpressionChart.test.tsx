import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  availableSamples,
  expressionValueDomain,
  hasNormalizedValues,
} from '@/lib/scientific/expression'
import {
  TP53_PATHWAY_EXPRESSION_FIXTURE,
  buildExpressionDataset,
} from '@/lib/scientific/expression.fixtures'
import { SERIES_COLORS } from '@/lib/scientific/geometry'
import { pointKeyToString } from '@/lib/scientific/types'
import type { ExpressionChartResult } from '@/lib/scientific/useExpressionChart'

import { ExpressionChart } from './ExpressionChart'

const TP53_TUMOR_1_KEY = pointKeyToString({ seriesId: 'tp53', pointId: 'TP53', sample: 'Tumor-1' })

function result(overrides: Partial<ExpressionChartResult> = {}): ExpressionChartResult {
  const data = TP53_PATHWAY_EXPRESSION_FIXTURE
  const base: ExpressionChartResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    dataset: data,
    samples: availableSamples(data),
    valueField: 'value',
    setValueField: vi.fn(),
    hasNormalizedValues: hasNormalizedValues(data),
    valueDomain: expressionValueDomain(data, 'value'),
    selectedKey: null,
    selectPoint: vi.fn(),
    clearSelection: vi.fn(),
  }
  return { ...base, ...overrides }
}

afterEach(() => {
  cleanup()
})

describe('ExpressionChart', () => {
  it('renders the chart heading and summary', () => {
    render(<ExpressionChart result={result()} />)
    expect(screen.getByText('Expression Chart')).toBeInTheDocument()
    expect(screen.getByText(/6 samples/)).toBeInTheDocument()
    expect(screen.getByText(/3 series/)).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(
      <ExpressionChart result={result({ status: 'loading', dataset: undefined, samples: [] })} />,
    )
    expect(screen.getByText('Loading expression data...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(
      <ExpressionChart result={result({ status: 'empty', dataset: undefined, samples: [] })} />,
    )
    expect(screen.getByText('No expression data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <ExpressionChart
        result={result({
          status: 'error',
          dataset: undefined,
          samples: [],
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load expression data')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders x-axis sample labels', () => {
    render(<ExpressionChart result={result()} />)
    for (const sample of ['Tumor-1', 'Tumor-3', 'Normal-3']) {
      expect(screen.getByText(sample)).toBeInTheDocument()
    }
  })

  it('renders every point as a keyboard-accessible selection control', () => {
    render(<ExpressionChart result={result()} />)
    const totalPoints = TP53_PATHWAY_EXPRESSION_FIXTURE.series.reduce(
      (sum, series) => sum + series.points.length,
      0,
    )
    expect(screen.getAllByRole('button', { name: /^Select / })).toHaveLength(totalPoints)
  })

  it('selects a point via click', () => {
    const selectPoint = vi.fn()
    render(<ExpressionChart result={result({ selectPoint })} />)
    fireEvent.click(screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ }))
    expect(selectPoint).toHaveBeenCalledWith(TP53_TUMOR_1_KEY)
  })

  it('supports keyboard selection via Enter and Space', () => {
    const selectPoint = vi.fn()
    render(<ExpressionChart result={result({ selectPoint })} />)
    const control = screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ })
    fireEvent.keyDown(control, { key: 'Enter' })
    expect(selectPoint).toHaveBeenCalledWith(TP53_TUMOR_1_KEY)

    cleanup()
    const selectPoint2 = vi.fn()
    render(
      <ExpressionChart
        result={result({ selectPoint: selectPoint2, selectedKey: TP53_TUMOR_1_KEY })}
      />,
    )
    const control2 = screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ })
    fireEvent.keyDown(control2, { key: ' ' })
    expect(selectPoint2).toHaveBeenCalledWith(null)
  })

  it('shows a hover tooltip with the mapped rows', () => {
    render(<ExpressionChart result={result()} />)
    fireEvent.mouseEnter(
      screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ }),
    )
    const tooltip = screen.getByTestId('chart-tooltip')
    expect(tooltip).toBeInTheDocument()
    expect(tooltip).toHaveTextContent('TP53')
    expect(tooltip).toHaveTextContent('Tumor-1')
    expect(tooltip).toHaveTextContent('128.4')
    expect(tooltip).toHaveTextContent('1.92')
  })

  it('renders a detail panel for a controlled selection', () => {
    render(<ExpressionChart result={result({ selectedKey: TP53_TUMOR_1_KEY })} />)
    expect(screen.getByTestId('chart-selection-detail')).toBeInTheDocument()
    expect(screen.getByText('TP53', { selector: 'h3' })).toBeInTheDocument()
    expect(screen.getByText('Value', { selector: 'dt' })).toBeInTheDocument()
  })

  it('clears the selection from the detail panel', () => {
    const clearSelection = vi.fn()
    render(<ExpressionChart result={result({ selectedKey: TP53_TUMOR_1_KEY, clearSelection })} />)
    fireEvent.click(screen.getByRole('button', { name: /clear selection/i }))
    expect(clearSelection).toHaveBeenCalledTimes(1)
  })

  it('renders the series legend', () => {
    render(<ExpressionChart result={result()} />)
    const legend = screen.getByTestId('chart-legend')
    expect(legend).toHaveTextContent('TP53')
    expect(legend).toHaveTextContent('MDM2')
    expect(legend).toHaveTextContent('BRCA1')
  })

  it('assigns series colors deterministically from the palette', () => {
    render(<ExpressionChart result={result()} />)
    // Fixture series are normalized to sorted order: brca1, mdm2, tp53.
    const first = screen.getByTestId('series-line-brca1')
    expect(first.getAttribute('stroke')).toBe(SERIES_COLORS[0])
  })

  it('toggles the value field when normalized values are available', () => {
    const setValueField = vi.fn()
    render(<ExpressionChart result={result({ setValueField })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Normalized' }))
    expect(setValueField).toHaveBeenCalledWith('normalizedValue')
  })

  it('hides the value-field toggle when no normalized values exist', () => {
    const single = buildExpressionDataset({
      series: [{ id: 's1', label: 'S1', points: [['Tumor-1', 1]] }],
    })
    render(
      <ExpressionChart
        result={result({
          dataset: single,
          samples: availableSamples(single),
          hasNormalizedValues: false,
          valueDomain: expressionValueDomain(single, 'value'),
        })}
      />,
    )
    expect(screen.queryByRole('button', { name: 'Normalized' })).not.toBeInTheDocument()
  })

  it('renders a single-point dataset without crashing', () => {
    const single = buildExpressionDataset({
      series: [{ id: 's1', label: 'S1', points: [['Tumor-1', 1]] }],
    })
    render(
      <ExpressionChart
        result={result({
          dataset: single,
          samples: availableSamples(single),
          valueDomain: expressionValueDomain(single, 'value'),
        })}
      />,
    )
    expect(screen.getByRole('button', { name: /Select S1/ })).toBeInTheDocument()
  })

  it('reports aria-pressed for selection, not hover', () => {
    render(<ExpressionChart result={result()} />)
    const control = screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ })
    fireEvent.mouseEnter(control)
    expect(control.getAttribute('aria-pressed')).toBe('false')
    fireEvent.mouseLeave(control)
    expect(control.getAttribute('aria-pressed')).toBe('false')
  })

  it('reports aria-pressed when selected', () => {
    render(<ExpressionChart result={result({ selectedKey: TP53_TUMOR_1_KEY })} />)
    const control = screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ })
    expect(control.getAttribute('aria-pressed')).toBe('true')
  })

  it('shows a visible focus ring when a point is keyboard-focused', () => {
    render(<ExpressionChart result={result()} />)
    const control = screen.getByRole('button', { name: /Select TP53: TP53 in Tumor-1 = 128.4/ })
    expect(screen.queryByTestId('point-tp53-TP53-Tumor-1-focus-ring')).not.toBeInTheDocument()
    fireEvent.focus(control)
    expect(screen.getByTestId('point-tp53-TP53-Tumor-1-focus-ring')).toBeInTheDocument()
    fireEvent.blur(control)
    expect(screen.queryByTestId('point-tp53-TP53-Tumor-1-focus-ring')).not.toBeInTheDocument()
  })

  it('renders metadata rows that collide with built-in labels', () => {
    const withCollidingMetadata: Parameters<typeof ExpressionChart>[0]['result']['dataset'] = {
      id: 'colliding',
      title: 'Colliding metadata',
      series: [
        {
          id: 's1',
          label: 'S1',
          points: [
            {
              identifier: 'TP53',
              sample: 'Tumor-1',
              value: 10,
              metadata: { Value: 'x', Sample: 'y', Normalized: 'z' },
            },
          ],
        },
      ],
    }
    render(
      <ExpressionChart
        result={result({
          dataset: withCollidingMetadata,
          samples: availableSamples(withCollidingMetadata),
          valueDomain: expressionValueDomain(withCollidingMetadata, 'value'),
        })}
      />,
    )
    const control = screen.getByRole('button', { name: /Select S1/ })
    fireEvent.mouseEnter(control)
    expect(screen.getByTestId('chart-tooltip')).toHaveTextContent('Value')
  })

  it('respects an explicit pixel width for responsive layouts', () => {
    render(<ExpressionChart result={result()} width={800} />)
    expect(screen.getByTestId('expression-chart-svg').getAttribute('width')).toBe('800')
  })
})
