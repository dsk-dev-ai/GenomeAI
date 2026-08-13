'use client'

import { useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import { createScale } from '@/lib/genome/geometry'
import type { GenomeViewport, VariantFeature } from '@/lib/genome/types'
import { type VariantTrackDefinition, useGenomeTrack } from '@/lib/genome/useGenomeBrowser'
import { variantAccessibleLabel, variantDetailLines, variantLabel } from '@/lib/genome/variant'
import {
  VARIANT_MARK_HALF_HEIGHT,
  layoutVariantMarks,
  variantRowY,
  variantTrackHeight,
  variantsInViewport,
} from '@/lib/genome/variantGeometry'

const SVG_WIDTH = 1000
const TRACK_HEADER_WIDTH = 96
const MARK_WIDTH = 2
const MARK_COLOR = '#0891b2'
const SELECTED_MARK_COLOR = '#db2777'

/**
 * Renders one lane of point variants (Phase 6.4).
 *
 * Variants are single-position records drawn as vertical marks positioned
 * with the shared Genome Browser scale, so they stay aligned with the axis.
 * Dense regions are stacked onto rows when marks would overlap. Each mark
 * carries a hover `<title>` and is a keyboard-focusable selection control;
 * selecting a variant reveals a readable detail panel beneath the lane.
 *
 * Owns its own track hook (called unconditionally); the browser passes the
 * discriminated `VariantTrackDefinition`, so `data` resolves to
 * `VariantFeature` records with no cast.
 */
export function VariantTrack({
  track,
  debouncedViewport,
}: {
  track: VariantTrackDefinition
  debouncedViewport: GenomeViewport
}) {
  const data = useGenomeTrack(track, debouncedViewport)
  const viewport = debouncedViewport
  const scale = createScale(viewport.start, viewport.end, SVG_WIDTH - TRACK_HEADER_WIDTH)
  const variants = variantsInViewport(data.data ?? [], viewport)
  const marks = layoutVariantMarks(scale, variants)

  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = selectedId !== null ? variants.find((v) => v.id === selectedId) : undefined
  const rows = marks.length > 0 ? Math.max(...marks.map((mark) => mark.row)) + 1 : 0
  const height = variantTrackHeight(rows)
  const title = `${data.label}: ${variants.length} ${variants.length === 1 ? 'variant' : 'variants'}`

  const handleSelect = (variant: VariantFeature) => {
    setSelectedId((current) => (current === variant.id ? null : variant.id))
  }

  return (
    <VisualizationContainer
      title={data.label}
      status={data.status}
      error={data.errorMessage ? { message: data.errorMessage } : undefined}
      loadingLabel={`Loading ${data.label.toLowerCase()}...`}
      emptyMessage={`No ${data.label.toLowerCase()} found in region.`}
      onRetry={data.refetch}
    >
      {data.status === 'success' ? (
        <>
          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${height}`}
            className="w-full"
            // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG would
            // otherwise be flagged as a <fieldset> candidate; group is correct here so
            // the interactive variant controls below stay in the a11y tree.
            role="group"
            aria-label={title}
            data-testid="variant-track"
          >
            {marks.map((mark) => {
              const isSelected = mark.variant.id === selectedId
              const x = TRACK_HEADER_WIDTH + mark.x
              const y = variantRowY(mark.row)
              return (
                <g key={mark.variant.id} data-testid={`variant-mark-${mark.variant.id}`}>
                  <title>{variantAccessibleLabel(mark.variant)}</title>
                  <line
                    x1={x}
                    y1={y - VARIANT_MARK_HALF_HEIGHT}
                    x2={x}
                    y2={y + VARIANT_MARK_HALF_HEIGHT}
                    stroke={isSelected ? SELECTED_MARK_COLOR : MARK_COLOR}
                    strokeWidth={isSelected ? 3 : MARK_WIDTH}
                  />
                  <rect
                    role="button"
                    aria-label={`Select ${variantAccessibleLabel(mark.variant)}`}
                    aria-pressed={isSelected}
                    tabIndex={0}
                    x={x - 4}
                    y={y - VARIANT_MARK_HALF_HEIGHT - 1}
                    width={9}
                    height={VARIANT_MARK_HALF_HEIGHT * 2 + 2}
                    fill="transparent"
                    data-variant-id={mark.variant.id}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        handleSelect(mark.variant)
                      }
                    }}
                    onClick={() => handleSelect(mark.variant)}
                  />
                </g>
              )
            })}
          </svg>
          {selected ? (
            <VariantDetail
              label={variantLabel(selected)}
              testId={`variant-detail-${selected.id}`}
              lines={variantDetailLines(selected)}
            />
          ) : null}
        </>
      ) : null}
    </VisualizationContainer>
  )
}

function VariantDetail({
  label,
  lines,
  testId,
}: {
  label: string
  lines: { label: string; value: string }[]
  testId: string
}) {
  return (
    <section
      aria-label={`${label} details`}
      className="mt-2 flex w-full flex-col gap-1 rounded-md border border-gray-200 bg-gray-50 p-3"
      data-testid={testId}
    >
      <span className="text-sm font-semibold text-gray-800">{label}</span>
      <dl className="m-0 grid w-full grid-cols-[auto_1fr] gap-x-4 gap-y-0.5">
        {lines.map((line) => (
          <div key={line.label} className="contents">
            <dt className="text-xs text-gray-500">{line.label}</dt>
            <dd className="text-xs text-gray-800">{line.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
