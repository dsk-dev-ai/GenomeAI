import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GenomeViewport } from '@/lib/genome/types'
import { TP53_WINDOW_COVERAGE_FIXTURE } from '@/lib/scientific/advanced.fixtures'
import { coverageDomain, coverageExtent } from '@/lib/scientific/coverage'
import type { CoverageChartResult } from '@/lib/scientific/useCoverageChart'

import { CoverageChart } from './CoverageChart'

const DATA = TP53_WINDOW_COVERAGE_FIXTURE
const CHROMOSOME = 'chr17'
const EXTENT = coverageExtent(DATA, CHROMOSOME) as { start: number; end: number }
const VIEWPORT: GenomeViewport = {
  chromosome: CHROMOSOME,
  start: EXTENT.start,
  end: EXTENT.end,
  bounds: { length: EXTENT.end },
}

function result(overrides: Partial<CoverageChartResult> = {}): CoverageChartResult {
  const base: CoverageChartResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    dataset: DATA,
    chromosomes: [CHROMOSOME],
    chromosome: CHROMOSOME,
    selectChromosome: vi.fn(),
    domain: coverageDomain(DATA, CHROMOSOME),
    viewport: VIEWPORT,
    zoom: vi.fn(),
    pan: vi.fn(),
    resetViewport: vi.fn(),
  }
  return { ...base, ...overrides }
}

afterEach(() => {
  cleanup()
})

describe('CoverageChart', () => {
  it('renders the chart heading and summary', () => {
    render(<CoverageChart result={result()} />)
    expect(screen.getByText('Coverage Chart')).toBeInTheDocument()
    expect(screen.getAllByText(/20 bins/).length).toBeGreaterThan(0)
    expect(screen.getAllByText('chr17').length).toBeGreaterThan(0)
  })

  it('renders the loading state with an accessible label', () => {
    render(
      <CoverageChart
        result={result({ status: 'loading', dataset: undefined, viewport: undefined })}
      />,
    )
    expect(screen.getByText('Loading coverage data...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(
      <CoverageChart
        result={result({ status: 'empty', dataset: undefined, viewport: undefined })}
      />,
    )
    expect(screen.getByText('No coverage data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <CoverageChart
        result={result({
          status: 'error',
          dataset: undefined,
          viewport: undefined,
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load coverage data')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders an area and a line path for the coverage values', () => {
    render(<CoverageChart result={result()} />)
    expect(screen.getByTestId('coverage-area')).toBeInTheDocument()
    expect(screen.getByTestId('coverage-line')).toBeInTheDocument()
  })

  it('renders one interactive bin per coverage bin', () => {
    render(<CoverageChart result={result()} />)
    expect(screen.getAllByRole('button', { name: /^Select / })).toHaveLength(DATA.bins.length)
  })

  it('shows a hover tooltip with the mapped bin value', () => {
    render(<CoverageChart result={result()} />)
    const bin = DATA.bins[0]
    fireEvent.mouseEnter(screen.getByTestId(`bin-${bin.start}-${bin.end}`))
    const tooltip = screen.getByTestId('chart-tooltip')
    expect(tooltip).toBeInTheDocument()
    expect(tooltip).toHaveTextContent('chr17')
    expect(tooltip).toHaveTextContent('Coverage')
    expect(tooltip).toHaveTextContent(String(bin.coverage))
  })

  it('renders chromosome and viewport navigation controls', () => {
    render(<CoverageChart result={result()} />)
    expect(screen.getByRole('group', { name: 'Chromosome' })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Viewport navigation' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zoom in' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zoom out' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pan left' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Pan right' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reset' })).toBeInTheDocument()
  })

  it('zooms in/out, pans, and resets through the view-model callbacks', () => {
    const zoom = vi.fn()
    const pan = vi.fn()
    const resetViewport = vi.fn()
    render(<CoverageChart result={result({ zoom, pan, resetViewport })} />)

    fireEvent.click(screen.getByRole('button', { name: 'Zoom in' }))
    expect(zoom).toHaveBeenCalledWith(0.5)

    fireEvent.click(screen.getByRole('button', { name: 'Zoom out' }))
    expect(zoom).toHaveBeenCalledWith(2)

    const span = EXTENT.end - EXTENT.start + 1
    fireEvent.click(screen.getByRole('button', { name: 'Pan left' }))
    expect(pan).toHaveBeenCalledWith(-span / 2)

    fireEvent.click(screen.getByRole('button', { name: 'Pan right' }))
    expect(pan).toHaveBeenCalledWith(span / 2)

    fireEvent.click(screen.getByRole('button', { name: 'Reset' }))
    expect(resetViewport).toHaveBeenCalledTimes(1)
  })

  it('selects a chromosome via the chromosome control', () => {
    const selectChromosome = vi.fn()
    const multi = {
      ...result(),
      chromosomes: ['chr17', 'chrX'],
      chromosome: 'chr17',
      selectChromosome,
    }
    render(<CoverageChart result={multi} />)
    fireEvent.click(screen.getByRole('button', { name: 'chrX' }))
    expect(selectChromosome).toHaveBeenCalledWith('chrX')
  })

  it('renders the selection detail panel with the coverage range', () => {
    render(<CoverageChart result={result()} />)
    const detail = screen.getByTestId('coverage-selection-detail')
    expect(detail).toBeInTheDocument()
    expect(detail).toHaveTextContent('Coverage range')
    expect(detail).toHaveTextContent('18')
  })

  it('respects an explicit pixel width for responsive layouts', () => {
    render(<CoverageChart result={result()} width={820} />)
    expect(screen.getByTestId('coverage-svg').getAttribute('width')).toBe('820')
  })

  it('renders without bins without crashing', () => {
    const empty = {
      ...result(),
      dataset: { id: 'empty', title: 'Empty', bins: [] },
      domain: undefined,
      viewport: undefined,
    }
    render(<CoverageChart result={empty} />)
    expect(screen.getByText('Coverage Chart')).toBeInTheDocument()
  })
})
