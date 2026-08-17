import { act, cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { P53_HELIX_STRUCTURE_FIXTURE } from './molecular.fixtures'
import { useMolecularStructureViewer } from './useMolecularStructureViewer'

function Harness({
  onResult,
  options = {},
}: {
  onResult: (result: ReturnType<typeof useMolecularStructureViewer>) => void
  options?: Parameters<typeof useMolecularStructureViewer>[0]
}) {
  const result = useMolecularStructureViewer(options)
  onResult(result)
  return <output data-testid="status">{result.status}</output>
}

function renderHook(options: Parameters<typeof useMolecularStructureViewer>[0] = {}) {
  let result: ReturnType<typeof useMolecularStructureViewer> | undefined
  render(
    <Harness
      options={options}
      onResult={(next) => {
        result = next
      }}
    />,
  )
  return {
    get result(): ReturnType<typeof useMolecularStructureViewer> {
      if (result === undefined) {
        throw new Error('useMolecularStructureViewer did not capture a result')
      }
      return result
    },
  }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('useMolecularStructureViewer', () => {
  it('loads a structure and reports success with a summary', async () => {
    const loader = vi.fn(async () => P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(1)
    expect(captured.result.structure?.id).toBe('fixture-mini-p53-helix')
    expect(captured.result.summary?.chains).toBe(1)
    expect(captured.result.summary?.atoms).toBeGreaterThan(0)
  })

  it('reports empty for a structure with no atoms', async () => {
    const loader = vi.fn(async () => ({ id: 'empty', chains: [], atoms: [], bonds: [] }))
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('empty'))
    expect(captured.result.structure).toBeDefined()
    expect(captured.result.summary).toBeUndefined()
  })

  it('reports error when the loader rejects and refetch retries', async () => {
    const loader = vi
      .fn()
      .mockRejectedValueOnce(new Error('structure down'))
      .mockResolvedValueOnce(P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.result.error?.message).toBe('structure down')

    captured.result.refetch()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(loader).toHaveBeenCalledTimes(2)
  })

  it('defaults to the cartoon representation and updates it', async () => {
    const loader = vi.fn(async () => P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.result.representation).toBe('cartoon')

    act(() => captured.result.setRepresentation('space-filling'))
    await waitFor(() => expect(captured.result.representation).toBe('space-filling'))
  })

  it('tracks visibility, defaulting to visible', async () => {
    const loader = vi.fn(async () => P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.result.visible).toBe(true)

    act(() => captured.result.setVisible(false))
    await waitFor(() => expect(captured.result.visible).toBe(false))
  })

  it('frames the camera around the structure centroid on load', async () => {
    const loader = vi.fn(async () => P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    expect(captured.result.focus).toBeDefined()
    expect(captured.result.focus?.radius).toBeGreaterThanOrEqual(1)
  })

  it('bumps the focus version on reset and fit', async () => {
    const loader = vi.fn(async () => P53_HELIX_STRUCTURE_FIXTURE)
    const captured = renderHook({ loader })
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('success'))
    const initial = captured.result.focus?.version ?? 0

    act(() => captured.result.resetView())
    await waitFor(() => expect(captured.result.focus?.version).toBe(initial + 1))

    act(() => captured.result.fitToView())
    await waitFor(() => expect(captured.result.focus?.version).toBe(initial + 2))
  })

  it('reports an error when no loader or structure id is provided', async () => {
    const captured = renderHook()
    await waitFor(() => expect(screen.getByTestId('status').textContent).toBe('error'))
    expect(captured.result.error?.message).toMatch(/No structure loader provided/)
  })
})
