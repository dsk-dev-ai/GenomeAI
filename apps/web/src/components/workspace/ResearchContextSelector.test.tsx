import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { PRESET_CONTEXTS, TP53_CONTEXT } from '@/lib/workspace/researchContext'

import { ResearchContextSelector } from './ResearchContextSelector'

afterEach(() => {
  cleanup()
})

describe('ResearchContextSelector', () => {
  it('renders a labeled context select with all preset options', () => {
    render(
      <ResearchContextSelector
        context={TP53_CONTEXT}
        contexts={PRESET_CONTEXTS}
        onSelectContext={vi.fn()}
        onNavigateRegion={vi.fn()}
      />,
    )
    const select = screen.getByRole('combobox', { name: 'Research context' })
    expect(select).toBeInTheDocument()
    for (const option of screen.getAllByRole('option')) {
      expect(PRESET_CONTEXTS.some((preset) => preset.label === option.textContent)).toBe(true)
    }
  })

  it('reports the active region in an aria-live output', () => {
    render(
      <ResearchContextSelector
        context={TP53_CONTEXT}
        contexts={PRESET_CONTEXTS}
        onSelectContext={vi.fn()}
        onNavigateRegion={vi.fn()}
      />,
    )
    expect(screen.getByTestId('active-context')).toHaveTextContent(
      'chr17:7,650,000-7,700,000 (TP53 locus (chr17))',
    )
  })

  it('calls onSelectContext when a preset is chosen', () => {
    const onSelectContext = vi.fn()
    render(
      <ResearchContextSelector
        context={TP53_CONTEXT}
        contexts={PRESET_CONTEXTS}
        onSelectContext={onSelectContext}
        onNavigateRegion={vi.fn()}
      />,
    )
    fireEvent.change(screen.getByRole('combobox', { name: 'Research context' }), {
      target: { value: 'brca1-locus' },
    })
    expect(onSelectContext).toHaveBeenCalledTimes(1)
    expect(onSelectContext).toHaveBeenCalledWith(PRESET_CONTEXTS[1])
  })

  it('navigates to a valid custom region', () => {
    const onNavigateRegion = vi.fn()
    render(
      <ResearchContextSelector
        context={TP53_CONTEXT}
        contexts={PRESET_CONTEXTS}
        onSelectContext={vi.fn()}
        onNavigateRegion={onNavigateRegion}
      />,
    )
    fireEvent.change(screen.getByRole('textbox', { name: 'Go to region' }), {
      target: { value: 'chr17:10-100' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(onNavigateRegion).toHaveBeenCalledTimes(1)
    expect(onNavigateRegion).toHaveBeenCalledWith({ chromosome: 'chr17', start: 10, end: 100 })
  })

  it('shows an alert for an invalid region and does not navigate', () => {
    const onNavigateRegion = vi.fn()
    render(
      <ResearchContextSelector
        context={TP53_CONTEXT}
        contexts={PRESET_CONTEXTS}
        onSelectContext={vi.fn()}
        onNavigateRegion={onNavigateRegion}
      />,
    )
    fireEvent.change(screen.getByRole('textbox', { name: 'Go to region' }), {
      target: { value: 'not-a-region' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(screen.getByRole('alert')).toHaveTextContent('Region must look like chr1:100000-200000.')
    expect(onNavigateRegion).not.toHaveBeenCalled()
  })
})
