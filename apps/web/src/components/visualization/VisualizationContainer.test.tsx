import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { VisualizationContainer } from './VisualizationContainer'

afterEach(() => {
  cleanup()
})

describe('VisualizationContainer', () => {
  it('renders the title and optional description', () => {
    render(
      <VisualizationContainer
        title="Genome Browser"
        description="Inspect features."
        status="success"
      >
        <div>content</div>
      </VisualizationContainer>,
    )

    expect(screen.getByRole('heading', { name: 'Genome Browser' })).toBeInTheDocument()
    expect(screen.getByText('Inspect features.')).toBeInTheDocument()
  })

  it('renders content when the status is success', () => {
    render(
      <VisualizationContainer title="Genome Browser" status="success">
        <div>track content</div>
      </VisualizationContainer>,
    )

    expect(screen.getByText('track content')).toBeInTheDocument()
  })

  it('does not render content while loading', () => {
    render(
      <VisualizationContainer title="Genome Browser" status="loading">
        <div>track content</div>
      </VisualizationContainer>,
    )

    expect(screen.queryByText('track content')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Loading...')
  })

  it('renders a custom loading label', () => {
    render(
      <VisualizationContainer
        title="Genome Browser"
        status="loading"
        loadingLabel="Fetching tracks..."
      >
        <div>content</div>
      </VisualizationContainer>,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Fetching tracks...')
  })

  it('renders the empty state with the provided message', () => {
    render(
      <VisualizationContainer
        title="Genome Browser"
        status="empty"
        emptyMessage="No samples match the selection."
      >
        <div>content</div>
      </VisualizationContainer>,
    )

    expect(screen.getByText('No samples match the selection.')).toBeInTheDocument()
  })

  it('renders the error state with the error message', () => {
    render(
      <VisualizationContainer
        title="Genome Browser"
        status="error"
        error={{ message: 'Service unavailable.' }}
      >
        <div>content</div>
      </VisualizationContainer>,
    )

    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Failed to load visualization')
    expect(alert).toHaveTextContent('Service unavailable.')
  })

  it('renders a retry button and calls it when clicked', () => {
    const onRetry = vi.fn()
    render(
      <VisualizationContainer
        title="Genome Browser"
        status="error"
        error={{ message: 'Service unavailable.' }}
        onRetry={onRetry}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })

  it('does not render a retry button when onRetry is omitted', () => {
    render(
      <VisualizationContainer title="Genome Browser" status="error" error={{ message: 'Nope.' }} />,
    )

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('exposes accessible semantics: region labeled by the heading', () => {
    render(
      <VisualizationContainer title="Genome Browser" status="success">
        <div>content</div>
      </VisualizationContainer>,
    )

    const section = screen.getByRole('region', { name: 'Genome Browser' })
    const heading = screen.getByRole('heading', { name: 'Genome Browser' })
    expect(section).toContainElement(heading)
  })

  it('treats the idle status as loading', () => {
    render(
      <VisualizationContainer title="Genome Browser" status="idle">
        <div>content</div>
      </VisualizationContainer>,
    )

    expect(screen.getByRole('status')).toHaveTextContent('Loading...')
  })
})
