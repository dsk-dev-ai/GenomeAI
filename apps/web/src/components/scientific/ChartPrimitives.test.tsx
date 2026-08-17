import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import type { PlotArea } from '@/lib/scientific/geometry'
import { createCategoryScale, createContinuousScale } from '@/lib/scientific/scale'

import { ChartAxes } from './ChartAxes'
import { ChartLegend } from './ChartLegend'
import { ChartTooltip, TOOLTIP_WIDTH } from './ChartTooltip'

const plot: PlotArea = { x0: 40, y0: 10, width: 300, height: 200 }

function categoryScale() {
  return createCategoryScale(['A', 'B'], [plot.x0, plot.x0 + plot.width])
}

function continuousScale() {
  return createContinuousScale([-2, 2], [plot.x0, plot.x0 + plot.width])
}

afterEach(() => {
  cleanup()
})

describe('ChartAxes', () => {
  it('renders gridlines, y ticks, and the x-axis baseline', () => {
    render(
      <ChartAxes
        plot={plot}
        xScale={categoryScale()}
        yScale={continuousScale()}
        yTicks={[0, 1, 2]}
      />,
    )
    expect(screen.getByTestId('chart-axes')).toBeInTheDocument()
    expect(screen.getByTestId('chart-grid')).toBeInTheDocument()
    expect(screen.getByTestId('chart-y-ticks')).toBeInTheDocument()
    expect(screen.getByTestId('chart-x-labels')).toBeInTheDocument()
  })

  it('renders optional axis captions', () => {
    render(
      <ChartAxes
        plot={plot}
        xScale={categoryScale()}
        yScale={continuousScale()}
        yTicks={[]}
        xLabel="Sample"
        yLabel="Expression value"
      />,
    )
    expect(screen.getByTestId('chart-x-label')).toHaveTextContent('Sample')
    expect(screen.getByTestId('chart-y-label')).toHaveTextContent('Expression value')
  })

  it('formats tick values through the provided formatter', () => {
    render(
      <ChartAxes
        plot={plot}
        xContinuousScale={continuousScale()}
        yScale={continuousScale()}
        yTicks={[1_000_000]}
        xTicks={[2_000_000]}
        formatValue={(value) => `${value / 1_000_000}M`}
      />,
    )
    expect(screen.getByTestId('chart-y-ticks')).toHaveTextContent('1M')
    expect(screen.getByTestId('chart-x-labels')).toHaveTextContent('2M')
  })
})

describe('ChartLegend', () => {
  it('renders each series as a labelled list item', () => {
    render(
      <ChartLegend
        items={[
          { id: 'tp53', label: 'TP53', color: '#red' },
          { id: 'brca1', label: 'BRCA1', color: '#blue' },
        ]}
      />,
    )
    const list = screen.getByRole('list', { name: 'Series legend' })
    expect(list).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items.map((item) => item.textContent)).toEqual(['TP53', 'BRCA1'])
  })

  it('renders nothing for an empty legend', () => {
    const { container } = render(<ChartLegend items={[]} />)
    expect(container.firstChild).toBeNull()
  })
})

describe('ChartTooltip', () => {
  const tooltip = {
    title: 'TP53',
    subtitle: 'Tumor-1',
    rows: [
      { label: 'Value', value: '4.2' },
      { label: 'Group', value: 'Tumor' },
    ],
  }

  it('renders as a tooltip with the point summary and labelled rows', () => {
    render(<ChartTooltip tooltip={tooltip} x={100} y={50} width={400} />)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByText('TP53')).toBeInTheDocument()
    expect(screen.getByText('Tumor-1')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('4.2')).toBeInTheDocument()
  })

  it('keeps the tooltip on-screen by clamping to the canvas width', () => {
    const { rerender } = render(<ChartTooltip tooltip={tooltip} x={1000} y={50} width={400} />)
    const nearEdge = screen.getByRole('tooltip')
    // Clamped so the tooltip's right edge sits on the canvas edge.
    expect(Number.parseInt(nearEdge.style.left, 10)).toBe(400 - TOOLTIP_WIDTH)

    rerender(<ChartTooltip tooltip={tooltip} x={-50} y={-50} width={400} />)
    const nearOrigin = screen.getByRole('tooltip')
    expect(Number.parseInt(nearOrigin.style.left, 10)).toBeGreaterThanOrEqual(4)
    expect(Number.parseInt(nearOrigin.style.top, 10)).toBeGreaterThanOrEqual(4)
  })
})
