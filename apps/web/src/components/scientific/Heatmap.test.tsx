import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TP53_PATHWAY_HEATMAP_FIXTURE } from '@/lib/scientific/advanced.fixtures'
import type { HeatmapDataset } from '@/lib/scientific/advancedTypes'
import { heatmapCellKey, heatmapColorScale, heatmapValueDomain } from '@/lib/scientific/heatmap'
import type { HeatmapResult } from '@/lib/scientific/useHeatmap'

import { Heatmap } from './Heatmap'

const KEY_TP53_TUMOR_1 = heatmapCellKey({ row: 'tp53', column: 'Tumor-1' })

function result(overrides: Partial<HeatmapResult> = {}): HeatmapResult {
  const data = TP53_PATHWAY_HEATMAP_FIXTURE
  const base: HeatmapResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    dataset: data,
    domain: heatmapValueDomain(data),
    colorScale: heatmapColorScale(heatmapValueDomain(data) ?? { min: -1, max: 1 }),
    selectedKey: null,
    selectCell: vi.fn(),
    clearSelection: vi.fn(),
  }
  return { ...base, ...overrides }
}

afterEach(() => {
  cleanup()
})

describe('Heatmap', () => {
  it('renders the chart heading and summary', () => {
    render(<Heatmap result={result()} />)
    expect(screen.getByText('Heatmap')).toBeInTheDocument()
    expect(screen.getByText('3 rows · 6 columns')).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(<Heatmap result={result({ status: 'loading', dataset: undefined })} />)
    expect(screen.getByText('Loading heatmap data...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(<Heatmap result={result({ status: 'empty', dataset: undefined })} />)
    expect(screen.getByText('No heatmap data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <Heatmap
        result={result({
          status: 'error',
          dataset: undefined,
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load heatmap data')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders a cell for every row/column pair with deterministic labels', () => {
    render(<Heatmap result={result()} />)
    const data = TP53_PATHWAY_HEATMAP_FIXTURE
    const expectedCells = data.rows.length * data.columns.length
    expect(screen.getAllByRole('button', { name: /^Select / })).toHaveLength(expectedCells)
    expect(screen.getByTestId('cell-tp53-Tumor-1')).toBeInTheDocument()
    expect(screen.getByTestId('cell-brca1-Normal-3')).toBeInTheDocument()
  })

  it('renders row and column labels', () => {
    render(<Heatmap result={result()} />)
    for (const label of ['TP53', 'MDM2', 'BRCA1', 'Tumor-1', 'Tumor-3', 'Normal-3']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it('colors a value via the color scale and a missing value distinctly', () => {
    const withMissing: HeatmapDataset = {
      id: 'with-missing',
      title: 'Missing values',
      rows: ['g1', 'g2'],
      columns: ['c1', 'c2'],
      values: [
        [1, undefined],
        [2, 3],
      ],
    }
    const domain = heatmapValueDomain(withMissing)
    render(
      <Heatmap
        result={result({
          dataset: withMissing,
          domain,
          colorScale: heatmapColorScale(domain ?? { min: 1, max: 3 }),
        })}
      />,
    )
    const present = screen.getByTestId('cell-g1-c1')
    const missing = screen.getByTestId('cell-g1-c2')
    expect(present).toBeInTheDocument()
    expect(missing).toBeInTheDocument()
    expect(present.getAttribute('fill')).not.toBe(missing.getAttribute('fill'))
    expect(screen.getByRole('button', { name: /g1 · c2 · no measurement/i })).toBeInTheDocument()
  })

  it('shows a hover tooltip with the mapped cell value', () => {
    render(<Heatmap result={result()} />)
    fireEvent.mouseEnter(screen.getByTestId('cell-tp53-Tumor-1'))
    const tooltip = screen.getByTestId('chart-tooltip')
    expect(tooltip).toBeInTheDocument()
    expect(tooltip).toHaveTextContent('TP53')
    expect(tooltip).toHaveTextContent('Tumor-1')
    expect(tooltip).toHaveTextContent('1.92')
  })

  it('selects a cell via click and exposes it as pressed', () => {
    const selectCell = vi.fn()
    render(<Heatmap result={result({ selectCell })} />)
    fireEvent.click(screen.getByTestId('cell-tp53-Tumor-1'))
    expect(selectCell).toHaveBeenCalledWith(KEY_TP53_TUMOR_1)
  })

  it('clears a selected cell on re-click', () => {
    const selectCell = vi.fn()
    render(<Heatmap result={result({ selectCell, selectedKey: KEY_TP53_TUMOR_1 })} />)
    fireEvent.click(screen.getByTestId('cell-tp53-Tumor-1'))
    expect(selectCell).toHaveBeenCalledWith(null)
  })

  it('supports keyboard selection via Enter and toggling via Space', () => {
    const selectCell = vi.fn()
    render(<Heatmap result={result({ selectCell })} />)
    const cell = screen.getByTestId('cell-tp53-Tumor-1')
    fireEvent.keyDown(cell, { key: 'Enter' })
    expect(selectCell).toHaveBeenCalledWith(KEY_TP53_TUMOR_1)

    cleanup()
    const selectCell2 = vi.fn()
    render(<Heatmap result={result({ selectCell: selectCell2, selectedKey: KEY_TP53_TUMOR_1 })} />)
    fireEvent.keyDown(screen.getByTestId('cell-tp53-Tumor-1'), { key: ' ' })
    expect(selectCell2).toHaveBeenCalledWith(null)
  })

  it('reports aria-pressed for the selected cell', () => {
    render(<Heatmap result={result({ selectedKey: KEY_TP53_TUMOR_1 })} />)
    expect(screen.getByTestId('cell-tp53-Tumor-1').getAttribute('aria-pressed')).toBe('true')
  })

  it('renders a detail panel for a controlled selection and clears it', () => {
    const clearSelection = vi.fn()
    render(<Heatmap result={result({ selectedKey: KEY_TP53_TUMOR_1, clearSelection })} />)
    expect(screen.getByTestId('heatmap-selection-detail')).toBeInTheDocument()
    expect(screen.getByText('TP53', { selector: 'h3' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /clear selection/i }))
    expect(clearSelection).toHaveBeenCalledTimes(1)
  })

  it('does not render the detail panel without a selection', () => {
    render(<Heatmap result={result()} />)
    expect(screen.queryByTestId('heatmap-selection-detail')).not.toBeInTheDocument()
  })

  it('respects an explicit pixel width for responsive layouts', () => {
    render(<Heatmap result={result()} width={700} />)
    expect(screen.getByTestId('heatmap-svg').getAttribute('width')).toBe('700')
  })
})
