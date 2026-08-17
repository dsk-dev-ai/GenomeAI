/**
 * Molecular viewer renderer contract (Phase 6.12).
 *
 * The React layer talks only to this interface. It decouples the component
 * and hook from Three.js: tests inject a fake `MolecularViewer` (or fake
 * renderer) and never need a GPU, while production uses
 * `createThreeViewer` from `lib/molecular/render/threeViewer.ts`.
 */

import type { Point3 } from '@/lib/molecular/geometry'
import type { RepresentationId } from '@/lib/molecular/representations'
import type { MolecularStructure } from '@/lib/molecular/types'

/** Minimal renderer surface the Three.js viewer relies on. */
export interface ThreeRenderer {
  domElement: HTMLCanvasElement
  setPixelRatio(ratio: number): void
  setSize(width: number, height: number): void
  setClearColor(color: number | string, alpha?: number): void
  setAnimationLoop(callback: ((time: number) => void) | null): void
  render(scene: unknown, camera: unknown): void
  dispose(): void
}

/** Options accepted when creating a Three.js viewer. */
export interface CreateThreeViewerOptions {
  /** Injectable renderer factory (defaults to `THREE.WebGLRenderer`). */
  createRenderer?: () => ThreeRenderer
}

/** The imperative 3D viewer surface used by the React component. */
export interface MolecularViewer {
  /** Builds (or rebuilds) the structure group for a representation. */
  setStructure(structure: MolecularStructure, representation: RepresentationId): void
  /** Rebuilds the structure group in another representation. */
  setRepresentation(representation: RepresentationId): void
  /** Shows or hides the structure group. */
  setVisible(visible: boolean): void
  /** Frames the camera around a target with the given radius (angstroms). */
  focusCamera(target: Point3, radius: number): void
  /** Handles an explicit container resize. */
  resize(width: number, height: number): void
  /** Disposes renderer, controls, geometries, materials, and listeners. */
  dispose(): void
}

/** Factory signature used to inject a viewer into the React component. */
export type CreateMolecularViewer = (
  container: HTMLElement,
  options?: CreateThreeViewerOptions,
) => MolecularViewer
