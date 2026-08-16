import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { EXPRESSION_DISTRIBUTION_FIXTURE } from '@/lib/scientific/advanced.fixtures'
import type { DistributionDataset } from '@/lib/scientific/advancedTypes'
import { distributionGroups, groupStatistics, groupWhiskers } from '@/lib/scientific/distribution'
import type { DistributionChartResult } from '@/lib/scientific/useDistributionChart'

import { DistributionChart } from './DistributionChart'

const DATA = EXPRESSION_DISTRIBUTION_FIXTURE

function result(overrides: Partial<DistributionChartResult> = {}): DistributionChartResult {
  const groups = distributionGroups(DATA)
  const statistics = groups.map((group) => ({
    group,
    summary: groupStatistics(DATA, group),
    whiskers: groupWhiskers(DATA, group),
  }))
  let min = Number.POSITIVE_INFINITY
  let max = Number.NEGATIVE_INFINITY
  for (const entry of statistics) {
    const summary = entry.summary
    if (summary === undefined) continue
    min = Math.min(min, summary.min)
    max = Math.max(max, summary.max)
  }
  const valueDomain = min === Number.POSITIVE_INFINITY ? { min: 0, max: 1 } : { min, max }
  const base: DistributionChartResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    dataset: DATA,
    groups,
    statistics,
    valueDomain,
  }
  return { ...base, ...overrides }
}

afterEach(() => {
  cleanup()
})

describe('DistributionChart', () => {
  it('renders the chart heading and summary', () => {
    render(<DistributionChart result={result()} />)
    expect(screen.getByText('Distribution Chart')).toBeInTheDocument()
    expect(screen.getByText(/2 groups/)).toBeInTheDocument()
    expect(screen.getByText(/17 values/)).toBeInTheDocument()
  })

  it('renders the loading state with an accessible label', () => {
    render(
      <DistributionChart result={result({ status: 'loading', dataset: undefined, groups: [] })} />,
    )
    expect(screen.getByText('Loading distribution data...')).toBeInTheDocument()
  })

  it('renders the empty state message', () => {
    render(
      <DistributionChart result={result({ status: 'empty', dataset: undefined, groups: [] })} />,
    )
    expect(screen.getByText('No distribution data to show.')).toBeInTheDocument()
  })

  it('renders the error state and retries', () => {
    const refetch = vi.fn()
    render(
      <DistributionChart
        result={result({
          status: 'error',
          dataset: undefined,
          groups: [],
          error: { message: 'Failed to fetch' },
          refetch,
        })}
      />,
    )
    expect(screen.getByText('Failed to load distribution data')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('renders one group control per group', () => {
    render(<DistributionChart result={result()} />)
    expect(screen.getAllByRole('button', { name: /^Select group / })).toHaveLength(2)
  })

  it('renders axis labels', () => {
    render(<DistributionChart result={result()} />)
    expect(screen.getByText('Group')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
  })

  it('shows a hover tooltip with the group summary statistics', () => {
    render(<DistributionChart result={result()} />)
    fireEvent.mouseEnter(screen.getByTestId('group-Normal'))
    const tooltip = screen.getByTestId('chart-tooltip')
    expect(tooltip).toBeInTheDocument()
    expect(tooltip).toHaveTextContent('Normal')
    expect(tooltip).toHaveTextContent('Count')
    expect(tooltip).toHaveTextContent('Median')
  })

  it('renders the group name in the tooltip title', () => {
    render(<DistributionChart result={result()} />)
    fireEvent.mouseEnter(screen.getByTestId('group-Tumor'))
    expect(screen.getByTestId('chart-tooltip')).toHaveTextContent('Tumor')
  })

  it('respects an explicit pixel width for responsive layouts', () => {
    render(<DistributionChart result={result()} width={640} />)
    expect(screen.getByTestId('distribution-svg').getAttribute('width')).toBe('640')
  })

  it('renders a single-group dataset without crashing', () => {
    const single: DistributionDataset = {
      id: 'single',
      title: 'Single group',
      values: [
        { group: 'G1', value: 1 },
        { group: 'G1', value: 2 },
        { group: 'G1', value: 3 },
      ],
    }
    const groups = distributionGroups(single)
    const statistics = groups.map((group) => ({
      group,
      summary: groupStatistics(single, group),
      whiskers: groupWhiskers(single, group),
    }))
    render(
      <DistributionChart
        result={result({
          dataset: single,
          groups,
          statistics,
          valueDomain: { min: 1, max: 3 },
        })}
      />,
    )
    expect(screen.getByTestId('group-G1')).toBeInTheDocument()
  })
})
