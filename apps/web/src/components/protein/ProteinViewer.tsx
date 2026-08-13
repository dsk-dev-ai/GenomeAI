'use client'

import { type FormEvent, useMemo, useState } from 'react'

import { VisualizationContainer } from '@/components/visualization/VisualizationContainer'
import {
  featureAccessibleLabel,
  featureDetailLines,
  featureLabel,
  featureTypeColor,
} from '@/lib/protein/features'
import {
  AXIS_HEIGHT,
  FEATURE_ROW_HEIGHT,
  LABEL_GUTTER,
  RESIDUE_LABEL_MIN_PX,
  SEQUENCE_ROW_HEIGHT,
  SVG_WIDTH,
  computeResidueTicks,
  createResidueScale,
  featureToPixels,
  layoutFeatureRows,
  proteinViewerHeight,
  residueCenterX,
  residueFontSize,
  residueLabelX,
  sequenceRowY,
} from '@/lib/protein/geometry'
import { residuesInWindow } from '@/lib/protein/sequence'
import type { ProteinViewerResult } from '@/lib/protein/useProteinViewer'
import { proteinViewportLength } from '@/lib/protein/viewport'
import { parseProteinRegion } from '@/lib/protein/viewport'

/** Pixel offset applied to every lane so bars clear the axis. */
const AXIS_BOTTOM = AXIS_HEIGHT + 6

/** Minimum bar width (px) before a feature label is drawn. */
const FEATURE_LABEL_MIN_PX = 40

/** Minimum hit-target width (px) for a feature's selection control. */
const FEATURE_HIT_MIN_PX = 6

/** Minimum window width before per-residue letters are rendered. */
const SEQUENCE_HINT = 'Zoom in to view residues'

function ProteinStatus({ result }: { result: ProteinViewerResult }) {
  const protein = result.protein
  if (protein === undefined) return null
  return (
    <output className="text-xs text-gray-500" aria-live="polite">
      Residues {result.viewport.start.toLocaleString('en-US')}–
      {result.viewport.end.toLocaleString('en-US')} of {protein.length.toLocaleString('en-US')}{' '}
      &middot; {protein.sequence.length} residues
    </output>
  )
}

function ProteinControls({ result }: { result: ProteinViewerResult }) {
  const [regionText, setRegionText] = useState('')
  const [regionError, setRegionError] = useState<string | null>(null)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const length = result.protein ? result.protein.length : proteinViewportLength(result.viewport)
    const parsed = parseProteinRegion(regionText, length)
    if (parsed.ok) {
      result.navigateTo(parsed.start, parsed.end)
      setRegionText('')
      setRegionError(null)
    } else {
      setRegionError(parsed.error)
    }
  }

  const controls = [
    { label: 'Zoom in', action: result.zoomIn, glyph: '+' },
    { label: 'Zoom out', action: result.zoomOut, glyph: '\u2212' },
    { label: 'Scroll left', action: result.panLeft, glyph: '\u2190' },
    { label: 'Scroll right', action: result.panRight, glyph: '\u2192' },
    { label: 'Reset view', action: result.resetView, glyph: '\u21BA' },
  ]

  return (
    <div className="flex w-full flex-wrap items-center gap-2">
      <fieldset
        className="flex items-center gap-1 border-0 p-0"
        aria-label="Residue viewport navigation"
      >
        <legend className="sr-only">Residue viewport navigation</legend>
        {controls.map((control) => (
          <button
            key={control.label}
            type="button"
            onClick={control.action}
            aria-label={control.label}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
          >
            {control.glyph}
          </button>
        ))}
      </fieldset>
      <form
        className="ml-auto flex items-center gap-2"
        onSubmit={handleSubmit}
        aria-label="Go to residue"
        noValidate
      >
        <label htmlFor="protein-residue-input" className="text-sm text-gray-600">
          Residues
        </label>
        <input
          id="protein-residue-input"
          type="text"
          value={regionText}
          onChange={(event) => {
            setRegionText(event.target.value)
            setRegionError(null)
          }}
          placeholder="e.g. 42 or 94-292"
          aria-invalid={regionError !== null}
          aria-describedby={regionError ? 'protein-residue-error' : undefined}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        />
        <button
          type="submit"
          className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-700 hover:bg-gray-50"
        >
          Go
        </button>
      </form>
      {regionError ? (
        <span id="protein-residue-error" role="alert" className="w-full text-sm text-red-600">
          {regionError}
        </span>
      ) : null}
    </div>
  )
}

function ProteinGlyph({ result }: { result: ProteinViewerResult }) {
  const protein = result.protein
  if (protein === undefined) return null

  const viewport = result.viewport
  const scale = createResidueScale(viewport)
  const pxPerResidue = scale.pxPerBase
  const rows = useMemo(() => layoutFeatureRows(protein.features), [protein.features])
  const rowCount = rows.length
  const height = proteinViewerHeight(rowCount)
  const seqY = sequenceRowY(rowCount) + SEQUENCE_ROW_HEIGHT / 2
  const residues = residuesInWindow(protein.sequence, viewport.start, viewport.end)
  const ticks = computeResidueTicks(viewport.start, viewport.end, 8)

  return (
    <svg
      viewBox={`0 0 ${SVG_WIDTH} ${height}`}
      className="w-full"
      // biome-ignore lint/a11y/useSemanticElements: role="group" on an SVG keeps the
      // interactive feature controls inside the accessibility tree (see GenomeBrowser).
      role="group"
      aria-label={`${protein.name}: ${protein.length} residues, ${protein.features.length} features, showing residues ${viewport.start}-${viewport.end}`}
    >
      {/* Residue axis */}
      <g>
        {ticks.map((tick, index) => {
          const x = LABEL_GUTTER + scale.toX(tick.position)
          return (
            <g key={`${tick.position}-${index}`}>
              <line x1={x} y1={AXIS_BOTTOM - 8} x2={x} y2={AXIS_BOTTOM} stroke="#cbd5e1" />
              {tick.major ? (
                <text x={x} y={AXIS_BOTTOM - 12} fontSize={11} fill="#64748b" textAnchor="middle">
                  {tick.label}
                </text>
              ) : null}
            </g>
          )
        })}
      </g>

      {/* Feature rows */}
      {rows.map((row) =>
        row.features.map((feature) => {
          const { span, visible } = featureToPixels(scale, viewport, feature)
          if (!visible) return null
          const x = LABEL_GUTTER + span.x
          const y = AXIS_BOTTOM + row.yOffset
          const isSelected = feature.id === result.selectedFeatureId
          const fill = featureTypeColor(feature.type)
          return (
            <g key={feature.id} data-testid={`feature-${feature.id}`}>
              <title>{featureAccessibleLabel(feature)}</title>
              <rect
                x={x}
                y={y}
                width={Math.max(1, span.width)}
                height={FEATURE_ROW_HEIGHT - 6}
                rx={2}
                fill={fill}
                stroke={isSelected ? '#0f172a' : 'none'}
                strokeWidth={isSelected ? 1.5 : 0}
              />
              {span.width >= FEATURE_LABEL_MIN_PX ? (
                <text
                  x={x + 4}
                  y={y + (FEATURE_ROW_HEIGHT - 6) / 2 + 3}
                  fontSize={10}
                  fill="#ffffff"
                  fontWeight={500}
                >
                  {featureLabel(feature)}
                </text>
              ) : null}
              {/* Selection control (keyboard-accessible) */}
              <rect
                role="button"
                aria-label={`Select ${featureAccessibleLabel(feature)}`}
                aria-pressed={isSelected}
                tabIndex={0}
                x={x}
                y={y}
                width={Math.max(FEATURE_HIT_MIN_PX, span.width)}
                height={FEATURE_ROW_HEIGHT}
                fill="transparent"
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    result.selectFeature(isSelected ? null : feature.id)
                  }
                }}
                onClick={() => result.selectFeature(isSelected ? null : feature.id)}
              />
            </g>
          )
        }),
      )}

      {/* Sequence lane */}
      <g>
        {pxPerResidue >= RESIDUE_LABEL_MIN_PX ? (
          <text
            x={LABEL_GUTTER}
            y={seqY}
            fontSize={residueFontSize(pxPerResidue)}
            fill="#334155"
            textAnchor="middle"
            fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
          >
            {residues.map((residue) => (
              <tspan key={residue.index} x={LABEL_GUTTER + residueCenterX(scale, residue.index)}>
                {residue.aminoAcid}
              </tspan>
            ))}
          </text>
        ) : (
          <text x={LABEL_GUTTER} y={seqY} fontSize={11} fill="#94a3b8" textAnchor="middle">
            {SEQUENCE_HINT}
          </text>
        )}
        {/* Per-residue number markers when spacing allows */}
        {pxPerResidue >= RESIDUE_LABEL_MIN_PX ? (
          <g fill="#94a3b8">
            {residues
              .filter((_, i) => (i + 1) % 10 === 0 || (i === 0 && pxPerResidue >= 20))
              .map((residue) => (
                <text
                  key={`num-${residue.index}`}
                  x={LABEL_GUTTER + residueLabelX(scale, residue.index)}
                  y={seqY + 14}
                  fontSize={8}
                  textAnchor="middle"
                >
                  {residue.index}
                </text>
              ))}
          </g>
        ) : null}
      </g>
    </svg>
  )
}

function SelectedFeatureDetail({ result }: { result: ProteinViewerResult }) {
  const protein = result.protein
  if (protein === undefined) return null
  const feature = protein.features.find((candidate) => candidate.id === result.selectedFeatureId)
  if (feature === undefined) return null

  const lines = featureDetailLines(feature)
  return (
    <section
      className="mt-3 flex w-full flex-col gap-1 rounded-md border border-gray-200 p-3"
      aria-labelledby="selected-feature-heading"
      data-testid="protein-feature-detail"
    >
      <h3 id="selected-feature-heading" className="text-sm font-semibold text-gray-900">
        {featureLabel(feature)}
      </h3>
      <dl className="grid w-full grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
        {lines.map((line) => (
          <div key={line.label} className="flex gap-2 text-sm">
            <dt className="text-gray-500">{line.label}</dt>
            <dd className="text-gray-900">{line.value}</dd>
          </div>
        ))}
      </dl>
      <button
        type="button"
        onClick={() => result.selectFeature(null)}
        className="mt-2 w-fit rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
      >
        Clear selection
      </button>
    </section>
  )
}

export interface ProteinViewerProps {
  /** View model produced by `useProteinViewer`. */
  result: ProteinViewerResult
  /** Container heading. */
  title?: string
}

/**
 * Protein sequence + annotation viewer (Phase 6.5).
 *
 * Consumes a `ProteinViewerResult` (from `useProteinViewer`) and renders the
 * full data lifecycle through the shared `VisualizationContainer`, then the
 * protein glyph: a residue-number axis, stacked feature rows (domains,
 * motifs, sites, ...) clipped to the visible window, and a residue-letter
 * lane that stays aligned with the features. Navigation (zoom/pan/reset/jump)
 * and feature selection are keyboard-accessible.
 *
 * This phase is the sequence/annotation foundation — it does NOT render 3D
 * molecular structures.
 */
export function ProteinViewer({ result, title = 'Protein Viewer' }: ProteinViewerProps) {
  return (
    <VisualizationContainer
      title={title}
      description={
        result.protein
          ? `${result.protein.name}${result.protein.organism ? ` · ${result.protein.organism}` : ''} · ${result.protein.length} residues · ${result.protein.features.length} features`
          : undefined
      }
      status={result.status}
      error={result.error}
      loadingLabel="Loading protein sequence..."
      emptyMessage="No protein sequence to show."
      errorTitle="Failed to load protein"
      onRetry={result.refetch}
    >
      {result.status === 'success' && result.protein ? (
        <div className="flex w-full flex-col gap-2">
          <ProteinStatus result={result} />
          <ProteinControls result={result} />
          <ProteinGlyph result={result} />
          <SelectedFeatureDetail result={result} />
        </div>
      ) : null}
    </VisualizationContainer>
  )
}
