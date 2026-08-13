/**
 * Development fixture for the Protein Viewer (Phase 6.5).
 *
 * The backend exposes protein identity + sequence (`GET /proteins/{id}`) but
 * **does not yet expose annotation features** (domains, motifs, active
 * sites, ...). This module provides a small, clearly isolated, typed fixture
 * that mimics what a future backend feature endpoint would return, so the
 * viewer, its layout math, and its tests can be developed now.
 *
 * ## Boundary
 *
 * This is a **development fixture, not a real API**. It lives apart from
 * production adapters (`lib/protein/api.ts`) and must be replaced by a real
 * feature source as soon as the backend exposes one. Records flow through
 * the same normalizers (`toProtein`, `toProteinFeature`) the adapters use,
 * so the seam is exercised exactly as production would. See
 * `docs/visualization/protein-viewer.md`.
 */

import { toProtein, toProteinFeature } from './api'
import { prepareFeatures } from './features'
import { sequenceLength } from './sequence'
import type { Protein } from './types'

/** N-terminal 120 residues of TP53 (P53), 1-based-aligned with UniProt P04637. */
const P53_N_TERMINAL =
  'MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQ'.slice(
    0,
    120,
  )

/** Raw protein record shaped like `GET /proteins/{id}` would return. */
const P53_RAW_RECORD = {
  id: '7f9b0b3e-0000-4000-8000-000000000001',
  protein_id: 'P04637',
  protein_name: 'Cellular tumor antigen p53',
  symbol: 'P53',
  accession: 'P04637',
  sequence: P53_N_TERMINAL,
  length: sequenceLength(P53_N_TERMINAL),
  organism: 'Homo sapiens',
  function: 'Acts as a tumor suppressor; induces cell-cycle arrest or apoptosis.',
} as const

/** Representative TP53 annotations (fixture, over the N-terminal fragment). */
const P53_FEATURE_RECORDS = [
  {
    id: 'feature-transactivation',
    start: 1,
    end: 42,
    type: 'region',
    label: 'Transactivation',
    description: 'N-terminal transactivation domain',
    metadata: { source: 'interpro', accession: 'IPR012345' },
  },
  {
    id: 'feature-proline-rich',
    start: 62,
    end: 92,
    type: 'region',
    label: 'Proline-rich',
    description: 'Proline-rich regulatory region',
  },
  {
    id: 'feature-dna-binding',
    start: 94,
    end: 120,
    type: 'domain',
    label: 'DNA-binding',
    description: 'Sequence-specific DNA-binding domain (N-terminal fragment)',
  },
  {
    id: 'feature-nls',
    start: 100,
    end: 110,
    type: 'motif',
    label: 'Nuclear localization signal',
  },
  {
    id: 'feature-active-site',
    start: 108,
    end: 108,
    type: 'active_site',
    label: 'Active site',
    description: 'DNA-binding contact residue',
  },
  {
    id: 'feature-binding-site',
    start: 94,
    end: 96,
    type: 'binding_site',
    label: 'DNA binding site',
  },
] as const

/** TP53-like protein used by demos and tests. */
export const P53_PROTEIN_FIXTURE: Protein = {
  ...toProtein({ ...P53_RAW_RECORD }),
  features: prepareFeatures(P53_FEATURE_RECORDS.map((record) => toProteinFeature(record))),
}

/** Builds a long, valid amino-acid sequence for windowing tests. */
export function buildLongSequence(residues: number): string {
  const block = 'ACDEFGHIKLMNPQRSTVWY'
  const repeated = block.repeat(Math.ceil(residues / block.length))
  return repeated.slice(0, residues)
}

/** A long synthetic protein that exercises viewport windowing. */
export const LONG_PROTEIN_FIXTURE: Protein = {
  id: 'fixture-long',
  proteinId: 'LONG001',
  name: 'Long synthetic protein (fixture)',
  sequence: buildLongSequence(1500),
  length: 1500,
  organism: 'synthetic',
  description: 'Development-only long sequence used to exercise windowing.',
  features: prepareFeatures([
    { id: 'long-feature-a', start: 1, end: 200, type: 'domain', label: 'Head domain' },
    { id: 'long-feature-b', start: 700, end: 900, type: 'motif', label: 'Middle motif' },
    { id: 'long-feature-c', start: 1300, end: 1500, type: 'transmembrane', label: 'Tail region' },
  ]),
}
