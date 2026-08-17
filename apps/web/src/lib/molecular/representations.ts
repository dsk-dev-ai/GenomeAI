/**
 * Structure representations (Phase 6.12).
 *
 * A small, extensible set of renderings the Molecular Structure Viewer can
 * draw. Representation ids are the extension point: the builder
 * (`lib/molecular/render/representationBuilder.ts`) switches on the id, and
 * the control catalog below drives the labelled representation select. New
 * representations are added by registering an option here and a builder
 * branch there.
 */

/** Identifier of a supported structure representation. */
export type RepresentationId = 'cartoon' | 'ball-and-stick' | 'space-filling'

/** A representation the viewer offers, with its control label. */
export interface RepresentationOption {
  id: RepresentationId
  /** Short label used in the representation select. */
  label: string
  /** Longer description for tooltips / documentation. */
  description: string
}

/** The full representation catalog, in control order. */
export const REPRESENTATIONS: readonly RepresentationOption[] = [
  {
    id: 'cartoon',
    label: 'Cartoon / ribbon',
    description: 'Trace the polymer backbone as a smooth ribbon through the C-alpha trace.',
  },
  {
    id: 'ball-and-stick',
    label: 'Ball and stick',
    description: 'Atoms as coloured spheres with covalent bonds drawn between them.',
  },
  {
    id: 'space-filling',
    label: 'Space filling',
    description: 'Atoms as van der Waals spheres, so the molecular surface is visible.',
  },
]

/** The representation shown when a structure first loads. */
export const DEFAULT_REPRESENTATION: RepresentationId = 'cartoon'

/** Type guard for a `RepresentationId`. */
export function isRepresentationId(value: unknown): value is RepresentationId {
  return value === 'cartoon' || value === 'ball-and-stick' || value === 'space-filling'
}

/** Short label for a representation id (falls back to the id itself). */
export function representationLabel(id: RepresentationId): string {
  return REPRESENTATIONS.find((option) => option.id === id)?.label ?? id
}
