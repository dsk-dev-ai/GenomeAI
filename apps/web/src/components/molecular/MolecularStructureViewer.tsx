'use client'

import { type ChangeEvent, useEffect, useRef } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import { createThreeViewer } from '@/lib/molecular/render/threeViewer'
import type { CreateMolecularViewer, MolecularViewer } from '@/lib/molecular/render/types'
import { REPRESENTATIONS, type RepresentationId } from '@/lib/molecular/representations'
import type { MolecularStructureViewerResult } from '@/lib/molecular/useMolecularStructureViewer'

/**
 * 3D molecular structure viewer (Phase 6.12).
 *
 * Renders a `MolecularStructure` through a Three.js viewer behind the shared
 * `VisualizationContainer` lifecycle. The viewer instance is created once per
 * mount and updated in place (structure, representation, visibility, camera
 * framing) so the renderer is never recreated unnecessarily, and it is fully
 * disposed on unmount.
 *
 * The WebGL canvas is a supplementary visual: the labelled controls and the
 * textual structure summary carry the keyboard/assistive interaction, and the
 * canvas itself is exposed as a labelled image (see the accessibility section
 * of `docs/visualization/molecular-structure.md`).
 */
export interface MolecularStructureViewerProps {
  /** View model produced by `useMolecularStructureViewer`. */
  result: MolecularStructureViewerResult
  /** Container heading. */
  title?: string
  /**
   * Viewer factory (defaults to the Three.js implementation). Inject a fake
   * in tests to drive the lifecycle without a GPU.
   */
  createViewer?: CreateMolecularViewer
}

function structureCanvasLabel(result: MolecularStructureViewerResult): string {
  const summary = result.summary
  if (summary === undefined) return '3D molecular structure'
  return [
    `3D structure of ${summary.name}`,
    `${summary.chains} chain${summary.chains === 1 ? '' : 's'}`,
    `${summary.residues} residues`,
    `${summary.atoms} atoms`,
    `${summary.bonds} bonds`,
  ].join(', ')
}

export function MolecularStructureViewer({
  result,
  title = 'Molecular Structure Viewer',
  createViewer = createThreeViewer,
}: MolecularStructureViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const viewerRef = useRef<MolecularViewer | null>(null)
  const createViewerRef = useRef<CreateMolecularViewer>(createViewer)
  createViewerRef.current = createViewer

  // Create the viewer once the success-state container exists; dispose it on
  // unmount (or when the component leaves the success state, e.g. refetch).
  const viewerCreatedRef = useRef(false)
  useEffect(() => {
    const container = containerRef.current
    if (container === null || viewerCreatedRef.current || result.status !== 'success') return
    viewerCreatedRef.current = true
    viewerRef.current = createViewerRef.current(container)
    return () => {
      viewerRef.current?.dispose()
      viewerRef.current = null
      viewerCreatedRef.current = false
    }
  }, [result.status])

  useEffect(() => {
    const viewer = viewerRef.current
    if (viewer === null || result.structure === undefined || result.status !== 'success') return
    viewer.setStructure(result.structure, result.representation)
  }, [result.status, result.structure, result.representation])

  useEffect(() => {
    const viewer = viewerRef.current
    if (viewer === null || result.focus === undefined) return
    viewer.focusCamera(result.focus.target, result.focus.radius)
  }, [result.focus])

  useEffect(() => {
    viewerRef.current?.setVisible(result.visible)
  }, [result.visible])

  function handleRepresentationChange(event: ChangeEvent<HTMLSelectElement>) {
    result.setRepresentation(event.target.value as RepresentationId)
  }

  return (
    <VisualizationContainer
      title={title}
      description={
        result.summary
          ? `${result.summary.name} · ${result.summary.chains} chain${result.summary.chains === 1 ? '' : 's'} · ${result.summary.residues} residues · ${result.summary.atoms} atoms · ${result.summary.bonds} bonds`
          : undefined
      }
      status={result.status}
      error={result.error}
      loadingLabel="Loading molecular structure..."
      emptyMessage="No molecular structure to display."
      errorTitle="Failed to load molecular structure"
      onRetry={result.refetch}
    >
      {result.status === 'success' && result.structure ? (
        <div className="flex w-full flex-col gap-3">
          <div
            ref={containerRef}
            className="h-96 w-full rounded-md border border-gray-200 bg-white"
            role="img"
            aria-label={structureCanvasLabel(result)}
          />
          <output
            className="text-xs text-gray-500"
            aria-live="polite"
            data-testid="structure-status"
          >
            {structureCanvasLabel(result)}
          </output>

          <div className="flex w-full flex-wrap items-center gap-3">
            <fieldset
              className="flex items-center gap-1 border-0 p-0"
              aria-label="3D viewport controls"
            >
              <legend className="sr-only">3D viewport controls</legend>
              <button
                type="button"
                onClick={result.resetView}
                aria-label="Reset view"
                title="Reset view (also fit the structure to the viewport)"
                className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
              >
                Reset view
              </button>
              <button
                type="button"
                onClick={result.fitToView}
                aria-label="Fit to structure"
                title="Fit the structure to the viewport"
                className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
              >
                Fit to structure
              </button>
            </fieldset>

            <label htmlFor="molecular-representation" className="text-sm text-gray-600">
              Representation
            </label>
            <select
              id="molecular-representation"
              value={result.representation}
              onChange={handleRepresentationChange}
              aria-label="Structure representation"
              className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700"
            >
              {REPRESENTATIONS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={() => result.setVisible(!result.visible)}
              aria-pressed={result.visible}
              aria-label={result.visible ? 'Hide structure' : 'Show structure'}
              className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
            >
              {result.visible ? 'Hide structure' : 'Show structure'}
            </button>
          </div>
        </div>
      ) : null}
    </VisualizationContainer>
  )
}
