import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { P53_HELIX_STRUCTURE_FIXTURE } from '@/lib/molecular/molecular.fixtures'
import type { MolecularViewer } from '@/lib/molecular/render/types'
import type { MolecularStructureViewerResult } from '@/lib/molecular/useMolecularStructureViewer'

import { MolecularStructureViewer } from './MolecularStructureViewer'

function result(
  overrides: Partial<MolecularStructureViewerResult> = {},
): MolecularStructureViewerResult {
  const base: MolecularStructureViewerResult = {
    status: 'success',
    error: undefined,
    refetch: vi.fn(),
    structure: P53_HELIX_STRUCTURE_FIXTURE,
    summary: {
      name: 'p53 N-terminal helix (synthetic fixture)',
      chains: 1,
      residues: 15,
      atoms: 60,
      bonds: 75,
    },
    representation: 'cartoon',
    setRepresentation: vi.fn(),
    visible: true,
    setVisible: vi.fn(),
    focus: { target: { x: 0, y: 0, z: 0 }, radius: 5, version: 0 },
    resetView: vi.fn(),
    fitToView: vi.fn(),
  }
  return { ...base, ...overrides }
}

function fakeViewer() {
  const viewer: MolecularViewer = {
    setStructure: vi.fn(),
    setRepresentation: vi.fn(),
    setVisible: vi.fn(),
    focusCamera: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  }
  const createViewer = vi.fn(() => viewer)
  return { viewer, createViewer }
}

afterEach(() => {
  cleanup()
})

describe('MolecularStructureViewer', () => {
  it('renders the canvas with a labelled image and a live summary', () => {
    const { createViewer } = fakeViewer()
    render(<MolecularStructureViewer result={result()} createViewer={createViewer} />)
    const canvas = screen.getByRole('img')
    expect(canvas).toBeInTheDocument()
    expect(canvas.getAttribute('aria-label')).toContain('15 residues')
    expect(screen.getByTestId('structure-status').textContent).toContain('60 atoms')
  })

  it('renders the loading state without creating a viewer', () => {
    const { createViewer } = fakeViewer()
    render(
      <MolecularStructureViewer
        result={result({ status: 'loading', structure: undefined })}
        createViewer={createViewer}
      />,
    )
    expect(screen.getByText('Loading molecular structure...')).toBeInTheDocument()
    expect(createViewer).not.toHaveBeenCalled()
  })

  it('renders the empty state message', () => {
    const { createViewer } = fakeViewer()
    render(
      <MolecularStructureViewer
        result={result({ status: 'empty', structure: undefined })}
        createViewer={createViewer}
      />,
    )
    expect(screen.getByText('No molecular structure to display.')).toBeInTheDocument()
    expect(createViewer).not.toHaveBeenCalled()
  })

  it('renders the error state and retries', () => {
    const { createViewer } = fakeViewer()
    const refetch = vi.fn()
    render(
      <MolecularStructureViewer
        result={result({
          status: 'error',
          error: { message: 'down' },
          structure: undefined,
          refetch,
        })}
        createViewer={createViewer}
      />,
    )
    expect(screen.getByText('Failed to load molecular structure')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(refetch).toHaveBeenCalledTimes(1)
    expect(createViewer).not.toHaveBeenCalled()
  })

  it('creates the viewer once and feeds it the structure and focus', () => {
    const { viewer, createViewer } = fakeViewer()
    render(<MolecularStructureViewer result={result()} createViewer={createViewer} />)
    expect(createViewer).toHaveBeenCalledTimes(1)
    expect(viewer.setStructure).toHaveBeenCalledWith(P53_HELIX_STRUCTURE_FIXTURE, 'cartoon')
    expect(viewer.focusCamera).toHaveBeenCalledWith({ x: 0, y: 0, z: 0 }, 5)
  })

  it('switches representation through the labelled select', () => {
    const { viewer, createViewer } = fakeViewer()
    const setRepresentation = vi.fn()
    render(
      <MolecularStructureViewer
        result={result({ setRepresentation })}
        createViewer={createViewer}
      />,
    )
    const select = screen.getByRole('combobox', { name: 'Structure representation' })
    fireEvent.change(select, { target: { value: 'space-filling' } })
    expect(setRepresentation).toHaveBeenCalledWith('space-filling')
    expect(viewer.setStructure).toHaveBeenCalledWith(P53_HELIX_STRUCTURE_FIXTURE, 'cartoon')
  })

  it('toggles visibility with an accessible pressed state', () => {
    const { viewer, createViewer } = fakeViewer()
    const setVisible = vi.fn()
    const { unmount } = render(
      <MolecularStructureViewer result={result({ setVisible })} createViewer={createViewer} />,
    )
    const toggle = screen.getByRole('button', { name: 'Hide structure' })
    expect(toggle.getAttribute('aria-pressed')).toBe('true')

    fireEvent.click(toggle)
    expect(setVisible).toHaveBeenCalledWith(false)
    expect(viewer.setVisible).toHaveBeenCalledWith(true)

    unmount()
  })

  it('re-frames the camera when the focus version changes', async () => {
    const { viewer, createViewer } = fakeViewer()
    const first = result()
    const { rerender } = render(
      <MolecularStructureViewer result={first} createViewer={createViewer} />,
    )
    expect(viewer.focusCamera).toHaveBeenCalledTimes(1)

    const refocused = result({ focus: { target: { x: 1, y: 1, z: 1 }, radius: 6, version: 1 } })
    rerender(<MolecularStructureViewer result={refocused} createViewer={createViewer} />)
    await waitFor(() => expect(viewer.focusCamera).toHaveBeenCalledTimes(2))
  })

  it('exposes reset and fit controls', () => {
    const { createViewer } = fakeViewer()
    const resetView = vi.fn()
    const fitToView = vi.fn()
    render(
      <MolecularStructureViewer
        result={result({ resetView, fitToView })}
        createViewer={createViewer}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Reset view' }))
    fireEvent.click(screen.getByRole('button', { name: 'Fit to structure' }))
    expect(resetView).toHaveBeenCalledTimes(1)
    expect(fitToView).toHaveBeenCalledTimes(1)
  })

  it('disposes the viewer on unmount', () => {
    const { viewer, createViewer } = fakeViewer()
    const { unmount } = render(
      <MolecularStructureViewer result={result()} createViewer={createViewer} />,
    )
    unmount()
    expect(viewer.dispose).toHaveBeenCalledTimes(1)
  })
})
