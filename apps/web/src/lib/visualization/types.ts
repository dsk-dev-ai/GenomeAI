/**
 * TypeScript types for the GenomeAI visualization foundation (Phase 6.1).
 *
 * These types describe the reusable building blocks that future
 * visualization modules (genome browser, gene/variant viewers, protein
 * viewer, network viewer, scientific charts) will build on. They are
 * intentionally minimal — only what the foundation needs today.
 */

/** Stable identifier for a visualization or visualization data set. */
export type VisualizationId = string

/**
 * Lifecycle status of a visualization data request.
 *
 * `idle` is the initial state before any load has been requested.
 * `empty` means the load succeeded but produced no data to render.
 */
export type VisualizationStatus = 'idle' | 'loading' | 'success' | 'error' | 'empty'

/** Display metadata shared by every visualization. */
export interface VisualizationMetadata {
  id: VisualizationId
  title: string
  description?: string
}

/** Explicit dimensions used when a visualization needs a fixed size. */
export interface VisualizationDimensions {
  width?: number
  height?: number
}

/** Error information surfaced by the visualization data layer. */
export interface VisualizationError {
  message: string
  code?: string
}

/**
 * Reference to where a visualization's data originates. Visualization
 * components must not reach into storage directly; they consume data
 * through a loader that resolves this reference via the GenomeAI API/SDK.
 */
export interface VisualizationDataSource {
  /** Kind of source, e.g. `api` or `module`. */
  kind: string
  /** Locator for the data, e.g. an API resource path or version. */
  reference: string
}

/**
 * Discriminated union describing the state of visualization data.
 *
 * `useVisualizationData` exposes the same state through separate
 * `status`/`data`/`error` fields; this union is for callers that want to
 * pass the whole state around as a single value.
 */
export type VisualizationDataState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: VisualizationError }
  | { status: 'empty' }
