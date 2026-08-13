/**
 * TypeScript types for the Protein Viewer (Phase 6.5).
 *
 * ## Coordinate conventions
 *
 * Protein residues are numbered **one-based and inclusive**, matching the
 * GenomeAI protein model: residue `1` is the N-terminal residue, and a
 * feature spanning `start..end` covers residues `start` through `end`
 * inclusive (`length = end - start + 1`). This deliberately mirrors the
 * Genome Browser's genomic coordinate convention (see
 * `lib/genome/types.ts`) so the two viewers share identical interval
 * semantics and can reuse the same pixel/interval utilities.
 *
 * A `ProteinViewport` is a window over residues `start..end` (1-based,
 * inclusive); `bounds.length` carries the full protein length so navigation
 * can clamp pan/zoom to `1..length` exactly like the Genome Browser clamps
 * to a contig.
 */

/** Free-form metadata carried by a protein feature. */
export type ProteinFeatureMetadata = Record<string, string | number | boolean>

/** Feature classes the viewer understands for default presentation. */
export type KnownProteinFeatureType =
  | 'domain'
  | 'motif'
  | 'active_site'
  | 'binding_site'
  | 'signal_peptide'
  | 'transmembrane'
  | 'secondary_structure'
  | 'region'
  | 'custom'

/**
 * Type of a protein feature. The known literals get default colours/labels;
 * any other string (e.g. a database-specific term) is preserved verbatim so
 * the viewer is not hard-wired to one annotation source.
 */
export type ProteinFeatureType = KnownProteinFeatureType | (string & {})

/** A single amino-acid residue, 1-based. */
export interface ProteinResidue {
  /** 1-based position in the sequence. */
  index: number
  /** One-letter amino-acid code (uppercase). */
  aminoAcid: string
}

/**
 * An annotation spanning a residue interval (domain, motif, active site,
 * binding site, signal peptide, transmembrane region, ...).
 */
export interface ProteinFeature {
  /** Stable identifier (React key + selection identity). */
  id: string
  /** 1-based inclusive start residue. */
  start: number
  /** 1-based inclusive end residue. */
  end: number
  /** Annotation class. */
  type: ProteinFeatureType
  /** Short display label, e.g. `DNA binding`. */
  label: string
  /** Optional free-text description. */
  description?: string
  /** Optional source accession, e.g. an InterPro id. */
  accession?: string
  /** Optional free-form detail carried without extra types. */
  metadata?: ProteinFeatureMetadata
}

/** A protein sequence with its stable identity and annotations. */
export interface Protein {
  /** Stable identifier (may be a database uuid or accession). */
  id: string
  /** Backend accession / protein id, e.g. `P04637`. */
  proteinId?: string
  /** Short display name, e.g. `P53` or `TP53`. */
  name: string
  /** Full amino-acid sequence. */
  sequence: string
  /** Protein length in residues (1-based count, `sequence.length`). */
  length: number
  /** Organism name, e.g. `Homo sapiens`. */
  organism?: string
  /** Optional free-text description / function. */
  description?: string
  /** Annotation features spanning residue intervals. */
  features: ProteinFeature[]
}

/**
 * The currently visible window over a protein's residues.
 *
 * Coordinates are 1-based inclusive; `bounds.length` is the full protein
 * length used to clamp navigation (structurally identical to the Genome
 * Browser viewport, so both share the same pan/zoom math).
 */
export interface ProteinViewport {
  /** 1-based inclusive first visible residue. */
  start: number
  /** 1-based inclusive last visible residue. */
  end: number
  /** Known full protein length used to clamp navigation. */
  bounds?: { length: number }
}

/** The mutable state a protein viewer manages (viewport + selection). */
export interface ProteinViewerState {
  viewport: ProteinViewport
  selectedFeatureId: string | null
}
