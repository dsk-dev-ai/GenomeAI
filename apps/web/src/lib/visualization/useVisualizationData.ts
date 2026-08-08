import { useCallback, useEffect, useRef, useState } from 'react'

import type { VisualizationError, VisualizationStatus } from './types'

/**
 * Loader signature used by the visualization data layer. Loaders receive an
 * `AbortSignal` and should abort their underlying request when it fires
 * (for example by passing it to `fetch`). A load thrown as a result of
 * cancellation is ignored by the hook.
 */
export type VisualizationLoader<T> = (signal: AbortSignal) => Promise<T>

export interface UseVisualizationDataOptions<T> {
  /**
   * Predicate applied to a successful load. When it returns `true` the
   * result status becomes `empty` instead of `success`.
   */
  isEmpty?: (data: T) => boolean
}

export interface UseVisualizationDataResult<T> {
  status: VisualizationStatus
  data: T | undefined
  error: VisualizationError | undefined
  /** Re-runs the load request, aborting any in-flight request. */
  refetch: () => void
}

const ABORT_ERROR_NAME = 'AbortError'

function normalizeError(reason: unknown): VisualizationError {
  if (reason instanceof Error) {
    return { message: reason.message }
  }
  if (typeof reason === 'string') {
    return { message: reason }
  }
  if (typeof reason === 'object' && reason !== null && 'message' in reason) {
    return { message: String((reason as { message: unknown }).message) }
  }
  return { message: 'Failed to load visualization data.' }
}

function isAbortError(reason: unknown): boolean {
  if (reason instanceof Error) {
    return reason.name === ABORT_ERROR_NAME
  }
  if (typeof reason === 'object' && reason !== null && 'name' in reason) {
    return (reason as { name?: unknown }).name === ABORT_ERROR_NAME
  }
  return false
}

/**
 * Small async data access for visualization components.
 *
 * Owns the lifecycle of a visualization data request: loading, success,
 * empty, and error states. Stale responses are ignored when a newer
 * request supersedes an in-flight one, and the underlying request is
 * aborted on unmount. Components never touch storage — they provide a
 * loader that resolves data through the GenomeAI API/SDK.
 */
export function useVisualizationData<T>(
  loader: VisualizationLoader<T>,
  options: UseVisualizationDataOptions<T> = {},
): UseVisualizationDataResult<T> {
  const [data, setData] = useState<T | undefined>(undefined)
  const [error, setError] = useState<VisualizationError | undefined>(undefined)
  const [status, setStatus] = useState<VisualizationStatus>('idle')

  const loaderRef = useRef(loader)
  const isEmptyRef = useRef(options.isEmpty)
  loaderRef.current = loader
  isEmptyRef.current = options.isEmpty

  const controllerRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)

  const refetch = useCallback(() => {
    const controller = new AbortController()
    controllerRef.current?.abort()
    controllerRef.current = controller
    const requestId = ++requestIdRef.current

    setData(undefined)
    setError(undefined)
    setStatus('loading')

    Promise.resolve()
      .then(() => loaderRef.current(controller.signal))
      .then(
        (resolved) => {
          if (requestId !== requestIdRef.current) return
          let isEmpty = false
          try {
            isEmpty = isEmptyRef.current ? isEmptyRef.current(resolved) : false
          } catch (predicateError) {
            if (requestId !== requestIdRef.current) return
            setError(normalizeError(predicateError))
            setStatus('error')
            return
          }
          setData(resolved)
          setStatus(isEmpty ? 'empty' : 'success')
        },
        (reason: unknown) => {
          if (requestId !== requestIdRef.current) return
          if (controller.signal.aborted && isAbortError(reason)) return
          setError(normalizeError(reason))
          setStatus('error')
        },
      )
  }, [])

  useEffect(() => {
    refetch()
    return () => {
      controllerRef.current?.abort()
      requestIdRef.current += 1
    }
  }, [refetch])

  return { status, data, error, refetch }
}
