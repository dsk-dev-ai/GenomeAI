'use client'

import { type FormEvent, useState } from 'react'

import { formatRegionLabel } from '@/lib/genome/geometry'
import { parseGenomeRegion } from '@/lib/genome/region'
import type { GenomicInterval } from '@/lib/genome/types'
import type { ResearchContext } from '@/lib/workspace/researchContext'

export interface ResearchContextSelectorProps {
  /** The active context (a preset, or a custom region context). */
  context: ResearchContext
  /** Preset contexts offered in the select. */
  contexts: readonly ResearchContext[]
  /** Called when the user picks a preset from the select. */
  onSelectContext: (context: ResearchContext) => void
  /** Called with a validated custom region from the region input. */
  onNavigateRegion: (interval: GenomicInterval) => void
}

/**
 * Research context selector (Phase 6.9). Lets a researcher pick a preset
 * context or load a custom region; both drive the context-aware workspace
 * panels. The region form reuses the shared Phase 6.2 region parser, and the
 * active region is announced via an `aria-live` output.
 */
export function ResearchContextSelector({
  context,
  contexts,
  onSelectContext,
  onNavigateRegion,
}: ResearchContextSelectorProps) {
  const [regionText, setRegionText] = useState('')
  const [regionError, setRegionError] = useState<string | null>(null)

  const isPreset = contexts.some((preset) => preset.id === context.id)
  const regionLabel = formatRegionLabel(
    context.region.chromosome,
    context.region.start,
    context.region.end,
  )

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const result = parseGenomeRegion(regionText)
    if (result.ok) {
      setRegionText('')
      setRegionError(null)
      onNavigateRegion(result.interval)
    } else {
      setRegionError(result.error.message)
    }
  }

  return (
    <div className="flex w-full flex-col gap-4 lg:flex-row lg:items-end">
      <div className="flex w-full flex-col gap-1 lg:max-w-xs">
        <label htmlFor="research-context" className="text-sm font-medium text-gray-700">
          Research context
        </label>
        <select
          id="research-context"
          data-testid="research-context-select"
          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
          value={context.id}
          onChange={(event) => {
            const preset = contexts.find((item) => item.id === event.target.value)
            if (preset !== undefined) onSelectContext(preset)
          }}
        >
          {contexts.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.label}
            </option>
          ))}
          {!isPreset ? <option value={context.id}>Custom: {context.label}</option> : null}
        </select>
        <output className="text-xs text-gray-500" aria-live="polite" data-testid="active-context">
          Active region: {regionLabel}
          {isPreset ? ` (${context.label})` : ''}
        </output>
      </div>

      <form
        className="flex w-full flex-col gap-1 lg:max-w-sm"
        aria-label="Load custom region"
        onSubmit={handleSubmit}
      >
        <label htmlFor="region-input" className="text-sm font-medium text-gray-700">
          Go to region
        </label>
        <div className="flex w-full gap-2">
          <input
            id="region-input"
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
            placeholder="chr1:100000-200000"
            value={regionText}
            aria-invalid={regionError !== null}
            aria-describedby={regionError !== null ? 'region-error' : undefined}
            onChange={(event) => setRegionText(event.target.value)}
          />
          <button
            type="submit"
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
          >
            Go
          </button>
        </div>
        {regionError !== null ? (
          <span id="region-error" role="alert" className="text-xs text-red-700">
            {regionError}
          </span>
        ) : null}
      </form>
    </div>
  )
}
