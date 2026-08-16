import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE } from '@/lib/scientific/advanced.fixtures'
import type { VolcanoDataset } from '@/lib/scientific/advancedTypes'
import type { VolcanoPlotResult } from '@/lib/scientific/useVolcanoPlot'
import { volcanoDomains } from '@/lib/scientific/volcano'

import { VolcanoPlot } from './VolcanoPlot'

function result(overrides: Partial<VolcanoPlotResult> = {}): VolcanoPlotResult {
  const data = DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE
  const base: VolcanoPlotResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    dataset: data,
    domains: volcanoDomains(data),
    thresholds: { effectThreshold: 1, significanceThreshold: 2 },
    selectedKey: null,
    selectPoint: vi.fn(),
    clearSelection: vi.fn(),
  }
  return { ...base, ...overrides }
}

afterEach(() => {
  cleanup()
})

describe('VolcanoPlot', () => {
  it('renders the chart heading and summary', () => {
    render(<VolcanoPlot result={result()} />)
    expect(screen.getByText('Volcano Plot')).toBeInTheDocument()
    expect(screen.getByText(/12 features tested/)).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(<VolcanoPlot result={result({ status: 'loading', dataset: undefined })} />)
    expect(screen.getByText('Loading volcano data...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(<VolcanoPlot result={result({ status: 'empty', dataset: undefined })} />)
    expect(screen.getByText('No volcano data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <VolcanoPlot
        result={result({
          status: 'error',
          dataset: undefined,
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load volcano data')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders a point for every feature as a keyboard-accessible control', () => {
    render(<VolcanoPlot result={result()} />)
    const data = DIFFERENTIAL_EXPRESSION_VOLCANO_FIXTURE
    expect(screen.getAllByRole('button', { name: /^Select / })).toHaveLength(data.points.length)
  })

  it('renders axis labels', () => {
    render(<VolcanoPlot result={result()} />)
    expect(screen.getByText('Effect size')).toBeInTheDocument()
    expect(screen.getByText('Significance')).toBeInTheDocument()
  })

  it('renders threshold lines when thresholds are set', () => {
    render(<VolcanoPlot result={result()} />)
    expect(screen.getByTestId('volcano-thresholds')).toBeInTheDocument()
  })

  it('renders no threshold lines when thresholds are disabled', () => {
    render(
      <VolcanoPlot
        result={result({
          thresholds: { effectThreshold: undefined, significanceThreshold: undefined },
        })}
      />,
    )
    expect(screen.getByTestId('volcano-thresholds').children.length).toBe(0)
  })

  it('shows a hover tooltip with the mapped point value', () => {
    render(<VolcanoPlot result={result()} />)
    fireEvent.mouseEnter(screen.getByTestId('point-TP53'))
    const tooltip = screen.getByTestId('chart-tooltip')
    expect(tooltip).toBeInTheDocument()
    expect(tooltip).toHaveTextContent('TP53')
    expect(tooltip).toHaveTextContent('1.6')
    expect(tooltip).toHaveTextContent('4.2')
  })

  it('selects a point via click and exposes it as pressed', () => {
    const selectPoint = vi.fn()
    render(<VolcanoPlot result={result({ selectPoint })} />)
    fireEvent.click(screen.getByTestId('point-TP53-hit'))
    expect(selectPoint).toHaveBeenCalledWith('TP53')
  })

  it('clears a selected point on re-click', () => {
    const selectPoint = vi.fn()
    render(<VolcanoPlot result={result({ selectPoint, selectedKey: 'TP53' })} />)
    fireEvent.click(screen.getByTestId('point-TP53-hit'))
    expect(selectPoint).toHaveBeenCalledWith(null)
  })

  it('supports keyboard selection via Enter', () => {
    const selectPoint = vi.fn()
    render(<VolcanoPlot result={result({ selectPoint })} />)
    fireEvent.keyDown(screen.getByTestId('point-TP53-hit'), { key: 'Enter' })
    expect(selectPoint).toHaveBeenCalledWith('TP53')
  })

  it('reports aria-pressed for the selected point', () => {
    render(<VolcanoPlot result={result({ selectedKey: 'TP53' })} />)
    expect(screen.getByTestId('point-TP53-hit').getAttribute('aria-pressed')).toBe('true')
  })

  it('renders a detail panel for a controlled selection and clears it', () => {
    const clearSelection = vi.fn()
    render(<VolcanoPlot result={result({ selectedKey: 'TP53', clearSelection })} />)
    expect(screen.getByTestId('volcano-selection-detail')).toBeInTheDocument()
    expect(screen.getByText('TP53', { selector: 'h3' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /clear selection/i }))
    expect(clearSelection).toHaveBeenCalledTimes(1)
  })

  it('does not render the detail panel without a selection', () => {
    render(<VolcanoPlot result={result()} />)
    expect(screen.queryByTestId('volcano-selection-detail')).not.toBeInTheDocument()
  })

  it('highlights points that pass the thresholds and leaves others base-colored', () => {
    render(<VolcanoPlot result={result()} />)
    // TP53 passes both thresholds; ESR1 passes neither.
    const tp53 = screen.getByTestId('point-TP53').querySelector('circle:first-of-type')
    const esr1 = screen.getByTestId('point-ESR1').querySelector('circle:first-of-type')
    expect(tp53?.getAttribute('fill')).toBe('#dc2626')
    expect(esr1?.getAttribute('fill')).toBe('#94a3b8')
  })

  it('shows a visible focus ring when a point is keyboard-focused', () => {
    render(<VolcanoPlot result={result()} />)
    const hit = screen.getByTestId('point-TP53-hit')
    expect(screen.queryByTestId('point-TP53-focus-ring')).not.toBeInTheDocument()
    fireEvent.focus(hit)
    expect(screen.getByTestId('point-TP53-focus-ring')).toBeInTheDocument()
    fireEvent.blur(hit)
    expect(screen.queryByTestId('point-TP53-focus-ring')).not.toBeInTheDocument()
  })

  it('respects an explicit pixel width for responsive layouts', () => {
    render(<VolcanoPlot result={result()} width={760} />)
    expect(screen.getByTestId('volcano-svg').getAttribute('width')).toBe('760')
  })

  it('renders a single-point dataset without crashing', () => {
    const single: VolcanoDataset = {
      id: 'single',
      title: 'Single point',
      points: [{ identifier: 'ONLY', effectSize: 1, significance: 3 }],
    }
    render(
      <VolcanoPlot
        result={result({
          dataset: single,
          domains: volcanoDomains(single),
        })}
      />,
    )
    expect(screen.getByRole('button', { name: /Select ONLY/ })).toBeInTheDocument()
  })
})
