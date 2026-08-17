/**
 * Molecular Structure Viewer view-model hook (Phase 6.12).
 *
 * Composes the Phase 6.1 visualization data lifecycle
 * (`useVisualizationData`) with representation selection, show/hide state,
 * and camera framing. The hook owns only **data and intent** — the 3D camera
 * lives in the renderer, so `focus` is a plain value
 * (`{ target, radius, version }`) the component applies to its viewer
 * whenever it changes (on load or on reset/fit).
 */

import { useCallback, useMemo, useState } from 'react'

import { fetchMolecularStructure } from '@/lib/molecular/api'
import { cameraFocusForStructure, structureSummary } from '@/lib/molecular/geometry'
import { DEFAULT_REPRESENTATION, type RepresentationId } from '@/lib/molecular/representations'
import type { MolecularStructure } from '@/lib/molecular/types'
import { isUsableStructure } from '@/lib/molecular/validate'
import type { VisualizationError, VisualizationStatus } from '@/lib/visualization/types'
import { useVisualizationData } from '@/lib/visualization/useVisualizationData'

/** Camera framing intent handed to the 3D viewer. */
export interface StructureFocus {
  target: { x: number; y: number; z: number }
  radius: number
  /** Bumped on every explicit reset/fit so the component re-frames. */
  version: number
}

/** Human-readable structure summary for status lines and the canvas label. */
export interface MolecularStructureSummary {
  name: string
  chains: number
  residues: number
  atoms: number
  bonds: number
}

/** Result shape consumed by `MolecularStructureViewer`. */
export interface MolecularStructureViewerResult {
  status: VisualizationStatus
  error: VisualizationError | undefined
  /** Re-runs the structure load request. */
  refetch: () => void
  /** Loaded structure, or `undefined` until success. */
  structure: MolecularStructure | undefined
  /** Derived human-readable summary of the loaded structure. */
  summary: MolecularStructureSummary | undefined
  /** Active representation. */
  representation: RepresentationId
  setRepresentation: (representation: RepresentationId) => void
  /** Whether the structure group is visible. */
  visible: boolean
  setVisible: (visible: boolean) => void
  /** Current camera framing intent (changes on load and on reset/fit). */
  focus: StructureFocus | undefined
  /** Re-frames the camera to fit the structure. */
  resetView: () => void
  /** Same as `resetView`; provided as the conventional "fit" control. */
  fitToView: () => void
}

export interface UseMolecularStructureViewerOptions {
  /** Loads a structure (defaults to nothing; a loader or id is required). */
  loader?: (signal: AbortSignal) => Promise<MolecularStructure>
  /** Future backend structure id used when no custom loader is provided. */
  structureId?: string
}

export function useMolecularStructureViewer(
  options: UseMolecularStructureViewerOptions = {},
): MolecularStructureViewerResult {
  const { loader: customLoader, structureId } = options

  const loader = useCallback(
    (signal: AbortSignal) => {
      if (customLoader !== undefined) return customLoader(signal)
      if (structureId !== undefined) {
        return fetchMolecularStructure(structureId, signal)
      }
      return Promise.reject(
        new Error('No structure loader provided to useMolecularStructureViewer.'),
      )
    },
    [customLoader, structureId],
  )

  const { status, data, error, refetch } = useVisualizationData<MolecularStructure>(loader, {
    isEmpty: (structure) => structure.atoms.length === 0,
  })

  const structure = data
  const [representation, setRepresentation] = useState<RepresentationId>(DEFAULT_REPRESENTATION)
  const [visible, setVisible] = useState(true)
  const [focusVersion, setFocusVersion] = useState(0)

  const summary = useMemo<MolecularStructureSummary | undefined>(() => {
    if (structure === undefined || !isUsableStructure(structure)) return undefined
    const computed = structureSummary(structure)
    return {
      name: computed.name,
      chains: computed.chains,
      residues: computed.residues,
      atoms: computed.atoms,
      bonds: computed.bonds,
    }
  }, [structure])

  const focus = useMemo<StructureFocus | undefined>(() => {
    if (structure === undefined || !isUsableStructure(structure)) return undefined
    const computed = cameraFocusForStructure(structure)
    return { target: computed.target, radius: computed.radius, version: focusVersion }
  }, [structure, focusVersion])

  const resetView = useCallback(() => setFocusVersion((version) => version + 1), [])
  const fitToView = useCallback(() => setFocusVersion((version) => version + 1), [])

  return {
    status,
    error,
    refetch,
    structure,
    summary,
    representation,
    setRepresentation,
    visible,
    setVisible,
    focus,
    resetView,
    fitToView,
  }
}
