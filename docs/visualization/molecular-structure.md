# Molecular Structure Viewer

Phase 6.12 introduces the first 3D rendering in the GenomeAI visualization
platform: an interactive molecular structure viewer at
`/visualization/molecular-structure` (linked from `/visualization`).

This document covers the scope, the Three.js design decision, the canonical
data model, the data boundary, the viewer lifecycle, accessibility, testing,
and future extensions.

## Scope

- Interactive 3D rendering of a molecular structure: orbit, zoom, and pan the
  camera (mouse drag / wheel / touch, via `OrbitControls`).
- Three representations, switchable at runtime:
  - **Cartoon / ribbon** — a smooth tube through the polymer backbone trace.
  - **Ball and stick** — CPK-coloured atoms as spheres with covalent bonds as
    cylinders.
  - **Space filling** — atoms as van der Waals spheres so the molecular
    surface is visible.
- Camera controls: **Reset view** and **Fit to structure** re-frame the camera
  around the structure; **Show/Hide structure** toggles the structure group.
- A live, human-readable structure summary (name, chains, residues, atoms,
  bonds) exposed both as a description and as a labelled `role="img"` canvas.
- The shared Phase 6.1 lifecycle (`loading` / `empty` / `error` + retry) via
  `VisualizationContainer`.

## Out of scope (deferred by design)

The viewer is a **visualization layer only**. It performs no docking, molecular
dynamics, folding, prediction, alignment, or analysis. It does not parse PDB /
MMCIF files directly (a future source adapter can — see
[Data boundary](#data-boundary)). It makes no claim about the biological
meaning of coordinates; it renders whatever the loader provides.

## Design decision: Three.js behind a pure seam

Phase 6.1–6.11 deliberately shipped without Three.js, Cytoscape.js, or D3.js,
deferring each to the milestone that truly requires it. A 3D molecular
structure viewer genuinely requires a 3D engine, so Phase 6.12 introduces
**Three.js** (`three`, runtime; `@types/three`, dev) — the only new runtime
dependency in the phase.

Why Three.js directly rather than a specialized molecular viewer library
(NGL, bio3d-viewer, Mol*):

- The repo convention is **minimal dependencies behind pure seams** (native
  scales instead of D3.js, a deterministic layout instead of Cytoscape.js).
  NGL/bio3d-viewer bring their own component, event, and state models on top
  of Three.js, which would fight the existing `useVisualizationData` /
  `VisualizationContainer` lifecycle.
- The required representations (cartoon ribbon, ball-and-stick, space-filling)
  are simple to build directly on core Three.js geometry
  (`TubeGeometry`, `SphereGeometry`, `CylinderGeometry`), giving full control
  over colors, materials, and — critically — resource disposal.
- WebGL stays **isolated** behind the `MolecularViewer` seam
  (`lib/molecular/render/types.ts`): the React layer never imports Three.js.
  `createThreeViewer` owns the scene, camera, controls, and renderer; tests
  inject a fake renderer and never touch a GPU, matching the repo's
  jsdom-testing convention.

Seam layout:

```
lib/molecular/types.ts                     canonical model (no deps)
lib/molecular/validate.ts                  pure validation (no deps)
lib/molecular/geometry.ts                  pure geometry (no deps)
lib/molecular/representations.ts           representation catalog (no deps)
lib/molecular/api.ts                       future GET /structures/{id} adapter
lib/molecular/molecular.fixtures.ts        dev fixture -> toStructure
lib/molecular/useMolecularStructureViewer.ts  view-model hook (React)
lib/molecular/render/types.ts              MolecularViewer interface
lib/molecular/render/representationBuilder.ts  pure Three.js object graph
lib/molecular/render/threeViewer.ts        WebGL implementation
components/molecular/MolecularStructureViewer.tsx  React component
app/visualization/molecular-structure/     route + demo
```

## Data model

`lib/molecular/types.ts` defines the canonical `MolecularStructure` model:

- `StructureAtom` — 1-based atom serial, element symbol, Cartesian **angstrom**
  coordinates, 1-based residue number, chain id, optional residue/atom names.
- `StructureBond` — two 1-based atom serials plus an optional bond order.
- `StructureResidue` — 1-based residue number, optional name, atom serials.
- `StructureChain` — chain id plus ordered residues.
- `MolecularStructure` — id, optional name/kind (`protein` | `nucleic-acid` |
  `other`)/organism/description/metadata, plus chains/atoms/bonds.

Conventions mirror the Phase 6.5 protein viewer (1-based residue numbering) and
the genome viewer (1-based, inclusive intervals): atom serials and residue
numbers are **one-based**, coordinates are in **angstroms**.

## Validation

`lib/molecular/validate.ts` reports structural issues rather than silently
rendering bad data:

- `structure.missing-id`, `structure.no-atoms`
- `atom.invalid-index` / `atom.duplicate-index` / `atom.non-finite-coordinates`
  / `atom.invalid-residue` / `atom.missing-element` / `atom.unreferenced`
- `bond.dangling` / `bond.self-loop` / `bond.duplicate`
- `chain.missing-id` / `residue.invalid-index` / `residue.duplicate-index` /
  `residue.dangling-atom`

`isUsableStructure` gates rendering; the hook only produces a summary and a
camera focus for usable structures.

## Geometry

`lib/molecular/geometry.ts` is pure and dependency-free:

- `elementPresentation` / `elementColor` — CPK-style colors and
  van der Waals / ball radii for C, N, O, S, H, P, FE, ZN, CL, BR, CA (with a
  safe default).
- `structureBounds` / `structureCentroid` / `structureRadius` /
  `cameraFocusForStructure` — camera framing (target + radius).
- `backboneTrace` — per-chain C-alpha-first trace for the cartoon ribbon.
- `elementCounts` / `structureSummary` — summaries for status lines and the
  accessible label.

## Data boundary

The GenomeAI backend **does not yet expose any molecular structure endpoint**.
The module follows the established Phase 6.5/6.6/6.7/6.8 fixture pattern:

- `lib/molecular/api.ts` documents the future contract
  (`GET /structures/{structure_id}`) and provides `toStructure`, the typed
  normalizer from raw records to `MolecularStructure`. A real endpoint can be
  wired in by pointing a loader at `fetchMolecularStructure` without touching
  the viewer, representations, or geometry.
- `lib/molecular/molecular.fixtures.ts` provides a **deterministically
  generated synthetic development fixture** (a small alpha-helix-like trace
  over TP53 N-terminal residues: backbone N/CA/C/O per residue plus a few side
  chains, with peptide and covalent bonds). It is generated in code (no random
  values), flows through the same `toStructure` normalizer production would
  use, and is clearly marked as synthetic (`metadata.source: 'fixture'`).

This keeps the seam honest: the moment a real structure source exists, the
fixture is replaced by a loader, and everything else stays.

## Viewer lifecycle

`useMolecularStructureViewer` composes the Phase 6.1 `useVisualizationData`
lifecycle with:

- `representation` / `setRepresentation` (default `cartoon`)
- `visible` / `setVisible`
- `focus` — `{ target, radius, version }` computed from the structure;
  `resetView` / `fitToView` bump `version` so the component re-frames the
  camera.

`MolecularStructureViewer` creates the Three.js viewer **once per mount** (and
only when the success-state container exists) using a `createdRef` guard, then
updates it in place via separate effects for structure/representation, focus,
and visibility. The viewer is fully disposed on unmount.

`render/threeViewer.ts` owns:

- `THREE.WebGLRenderer` (antialiased, alpha background) with an injectable
  factory.
- A `PerspectiveCamera` framed by `focusCamera` (distance ∝ structure radius,
  near/far from radius).
- `OrbitControls` with damping, ambient + key + fill lights.
- A `ResizeObserver` for responsive sizing and an animation loop.
- `dispose()` — stops the loop, disposes controls, geometries/materials
  (`disposeGroup`), the renderer, and detaches the canvas.

`render/representationBuilder.ts` builds only Three.js objects (groups,
geometries, materials) and is safe to test in jsdom; only the renderer touches
WebGL.

## Accessibility

The WebGL canvas is a supplementary visual; the controls and the textual
summary carry the keyboard/assistive interaction:

- The canvas container is `role="img"` with a descriptive `aria-label`
  (structure name, chains, residues, atoms, bonds), and the same summary is
  repeated in an `aria-live="polite"` output for updates.
- All controls are labelled buttons/selects with descriptive names:
  **Reset view**, **Fit to structure**, a labelled **Representation** select,
  and a **Show/Hide structure** toggle with `aria-pressed`.
- Loading / empty / error states reuse the shared `VisualizationContainer`
  semantics (labelled loading, message, retry button).

Known limitation: orbit/zoom/pan is pointer-driven; there is no keyboard
camera manipulation, so the textual summary is the assistive window into the
3D scene. Extending keyboard camera control is a documented future extension.

## Testing

84 new web tests, all running in jsdom (no GPU):

- `validate.test.ts` — every validation code, plus `isUsableStructure` /
  `firstStructureError`.
- `geometry.test.ts` — element presentation, bounds, centroid, radius, camera
  framing, backbone traces, element counts, summaries.
- `representations.test.ts` — catalog, default, type guard, labels.
- `api.test.ts` — `toStructure` normalization, malformed-record dropping,
  field fallbacks, metadata filtering; `fetchMolecularStructure` success /
  non-2xx / invalid-payload / invalid-structure with a mocked `fetch`.
- `molecular.fixtures.test.ts` — the fixture is valid, deterministic, and
  clearly synthetic.
- `render/representationBuilder.test.ts` — mesh counts per representation and
  full disposal of geometries/materials.
- `render/threeViewer.test.ts` — fake-renderer lifecycle: canvas attach, frame
  loop, camera framing distances, resize, dispose/detach.
- `useMolecularStructureViewer.test.tsx` — success / empty / error + retry,
  representation, visibility, focus versions, missing-loader error.
- `MolecularStructureViewer.test.tsx` — injected fake viewer: create-once,
  `setStructure`/`focusCamera`, representation select, visibility toggle,
  reset/fit controls, dispose on unmount, loading/empty/error states.

## Extensions

- Parse real structure formats (PDB / MMCIF) in a future source adapter and
  normalize through `toStructure`.
- More representations (licorice, surface/mesh, CA trace) by adding a
  `RepresentationId` catalog entry and a builder branch.
- Keyboard camera control and focus/search to pick atoms or residues.
- Multi-structure comparison or structure alignments (analysis, separate
  milestone).
- Render structures from the workspace by reusing this component behind a
  `WorkspaceDataSource` provider, mirroring the Phase 6.9 panel pattern.
