# Biological Network Viewer (Phase 6.6)

Renders a typed biological relationship graph (genes, proteins, variants,
diseases, drugs, transcripts, ...) as an interactive 2D SVG: a deterministic
layout, pan/zoom/fit navigation, node/edge selection, and node/edge-type
filtering. It follows the same layered architecture as the earlier
visualization milestones — pure, unit-tested math under `lib/network`, a thin
view-model hook, and a presentation-only component over the shared
[Phase 6.1 foundation](README.md).

## Status

Implemented on branch `feat/visualization-network-viewer`.

## Design decision: deterministic pure-SVG layout (no Cytoscape.js)

The Phase 6.1 technology notes anticipated Cytoscape.js for Phase 6.6. This
milestone deliberately delivers the network **foundation without that
dependency**: a deterministic **concentric** layout computed in TypeScript and
rendered with plain SVG, consistent with the platform's lightweight stance
("no C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, or D3.js — those are
introduced only when the milestone that actually requires them arrives").

Consequences and rationale:

- **Determinism first.** "Same input, stable output" is a hard requirement for
  scientific visualization and for tests. The concentric layout is fully
  deterministic (degree-descending rings, even angle spacing, golden-angle
  ring offset) with no PRNG, so screenshots and tests are reproducible.
- **Zero new dependencies.** The web app remains React + TypeScript + Tailwind
  + SVG.
- **A clean seam.** `createLayout` / `LAYOUT_STRATEGIES` behind the
  `LayoutStrategy` interface; force-directed, hierarchical, or Cytoscape.js
  layouts can be added later without touching the component or the hook.
- If interactive graph manipulation (drag-to-rearrange, physics, large graphs
  with WebGL) becomes a real requirement, the seam is where Cytoscape.js or a
  WebGPU renderer would plug in.

## Scope (delivered)

- Typed domain model (`lib/network/types.ts`): `Graph`, `GraphNode`,
  `GraphEdge`, `GraphLayout`, `GraphPoint`, `NetworkViewport`, `GraphFilter`,
  `GraphViewerState` — node/edge `type`s are opaque strings, so the viewer is
  not hard-wired to one annotation source.
- Pure model helpers (`lib/network/model.ts`): lookups, degree, available
  node/edge types, graph validation.
- Pure normalization (`lib/network/normalize.ts`): dedupe ids, drop
  self-loops and dangling edges, deterministic ordering.
- Pure filtering (`lib/network/filter.ts`): node/edge-type filters with
  no-dangling-edge guarantees.
- Pure deterministic layout (`lib/network/layout.ts`): concentric rings by
  degree (hubs in the centre), bounding-box computation, pluggable strategy
  registry (`createLayout`).
- Pure 2D viewport (`lib/network/viewport.ts`): identity/fit viewports,
  clamped pan/zoom, project point; `ZOOM_FACTOR` mirrors the genome/protein
  viewers.
- Pure render geometry (`lib/network/geometry.ts`): SVG constants, edge
  endpoints (inset to node edges), edge midpoint, node hit boxes.
- Presentation helpers (`lib/network/labels.ts`): default colours for known
  node/edge types, display + accessible labels, detail-panel rows.
- Thin typed adapter (`lib/network/api.ts`): documented expected contract for
  a future `GET /networks/{id}` endpoint plus normalization seams —
  **no backend changes** (see [API limitation](#api-limitation)).
- `useNetworkViewer` hook: load lifecycle (via the shared 6.1
  `useVisualizationData`), deterministic layout, viewport, filter, selection.
- `NetworkViewer` component: pan/zoom/fit SVG, wheel zoom, drag-to-pan,
  keyboard-accessible node/edge selection, node/edge-type filter controls,
  and a readable detail panel.
- Demo integrated at `/visualization` (`NetworkDemo`).
- Tests (98 across the network modules) and docs.

## Out of scope (later milestones or explicitly excluded)

- **Interactive graph manipulation** (drag-to-rearrange, physics, pinning) —
  deferred; the layout seam makes this additive.
- Cytoscape.js / D3.js / WebAssembly / WebGPU (see design decision above).
- Backend network/relationship endpoints (see
  [API limitation](#api-limitation)).
- Large-graph performance work (deferred to 6.9; see the roadmap).
- Import from external biological databases (STRING, Reactome, BioGRID,
  IntAct, Open Targets, ...). The browser never talks to them; they feed
  GenomeAI through the later connector/ingestion architecture.

## Coordinate conventions

Layout coordinates are **abstract 2D units** in a deterministic layout space
centred on the origin. A `NetworkViewport` projects a layout point `p` to
screen `(p.x * scale + x, p.y * scale + y)`. Layout is computed once per
graph; pan/zoom only move the viewport, so filtering never changes positions
(the layout is always derived from the **full** graph).

## Architecture and data flow

```text
NetworkViewer (component)                   apps/web/src/components/network/NetworkViewer.tsx
  useNetworkViewer (view model)             apps/web/src/lib/network/useNetworkViewer.ts
    useVisualizationData (lifecycle)        + reuse lib/visualization/useVisualizationData.ts (6.1)
    fetchNetworkGraph (adapter)             + lib/network/api.ts
      -> GET /networks/{id}                 + reuse lib/genome/api.ts (API_BASE_URL, errors)
    createLayout (deterministic)            + lib/network/layout.ts
    filterGraph (filtering)                 + lib/network/filter.ts
    fitViewport / pan / zoom                + lib/network/viewport.ts
  edgeScreenPoints / nodeScreenBox          + lib/network/geometry.ts
  labels / detail rows                      + lib/network/labels.ts
```

`NetworkViewer` is fully controlled by a `NetworkViewerResult` returned from
`useNetworkViewer`; the component renders nothing but presentation, so the
data lifecycle (loading / success / empty / error / retry) is handled by the
shared `VisualizationContainer`.

## Navigation, filtering, and selection

- **Fit-to-view** on load: the viewport is computed from the layout bounding
  box and the SVG size (`fitViewport`), so the whole network is visible.
- **Zoom** (`zoomIn` / `zoomOut` / wheel `zoomAt`) scales around a screen
  point and clamps to `MIN_GRAPH_SCALE..MAX_GRAPH_SCALE`; **pan** (buttons or
  drag) moves in screen pixels.
- **Filtering**: node-type and relationship-type selects (from the graph's
  available types) rebuild `filteredGraph` via `filterGraph`; the layout stays
  fixed. Edges whose endpoints are filtered out are dropped (no dangling
  edges). A "Clear filters" control resets.
- **Selection**: clicking or focusing a node/edge (Enter/Space) toggles its
  selection (node and edge selection are mutually exclusive); the selected
  item is outlined, announced via `aria-pressed`, and described in a labelled
  detail panel (`nodeDetailLines` / `edgeDetailLines`).

Because the whole graph is loaded once per network id, navigation, filtering,
and selection never refetch.

## API limitation

The GenomeAI backend does **not** yet expose a network endpoint. Therefore:

- `lib/network/api.ts` documents the expected contract (`RawGraphRecord` /
  `RawGraphNodeRecord` / `RawGraphEdgeRecord`), provides the normalization
  seams (`toGraphNode`, `toGraphEdge`, `graphFromRecords`), and
  `fetchNetworkGraph` attempts `GET /networks/{id}` (which 404s today,
  surfacing the limitation as a typed `GenomeApiError`).
- The isolated development fixture in `lib/network/network.fixtures.ts`
  supplies representative TP53 relationships today. It lives apart from
  production adapters, flows through the **same** normalizers the adapters
  use, and must be replaced — not treated as a real API — as soon as the
  backend exposes a network endpoint.

## Type representation

Node/edge `type`s are carried as opaque strings and mapped only for
presentation (`labels.ts`): known literals (gene, protein, variant, disease,
drug, ... for nodes; interacts_with, regulates, targets, ... for edges) get
stable default colours, and any other string is preserved verbatim with a
fallback colour. The viewer never infers a node class or relationship from
labels, and it never asserts scientific validity.

## Accessibility

- The SVG is a labelled group (`role="group"`, `aria-label` summarizing the
  network and visible node/edge counts) so the interactive node/edge controls
  stay in the accessibility tree.
- Each node and edge has a keyboard-focusable selection control
  (`role="button"`, `tabIndex=0`) with an accessible name (e.g. `Select TP53,
  gene` / `Select edge: TP53 encodes P53`); Enter/Space toggles selection,
  `aria-pressed` announces state, and a native `<title>` tooltip mirrors the
  detail.
- The detail panel is a labelled `<section>` with a `<dl>` of typed fields.
- Navigation and filter controls have accessible names; the summary is
  announced via `aria-live="polite"`.

## Tests

`apps/web` root test run (`pnpm --filter @genomeai/web test`) covers:

| Layer | File(s) | Focus |
|-------|---------|-------|
| model | `model.test.ts` | lookups, degree, available types, graph validation |
| normalize | `normalize.test.ts` | dedupe, self-loop/dangling removal, deterministic ordering |
| filter | `filter.test.ts` | node/edge filters, no dangling edges, combination, active-state |
| layout | `layout.test.ts` | concentric determinism, hub at centre, ring ordering, bounding boxes, strategy registry |
| viewport | `viewport.test.ts` | identity/clamp, projection, pan, zoom-around-point, fit-to-view |
| geometry | `geometry.test.ts` | edge endpoint insets, midpoint, screen projection, node hit boxes |
| labels | `labels.test.ts` | type colours, display/accessible labels, detail rows |
| api | `api.test.ts` | record normalization, invalid-record handling, URL, error mapping, fixture integrity |
| hook | `useNetworkViewer.test.tsx` | lifecycle states, fit-to-view, layout stability under filters, zoom/pan/fit, selection, reset-on-new-graph |
| component | `NetworkViewer.test.tsx` | rendering, node/edge selection (click + keyboard), detail panels, filter controls, empty-filter message |

The pre-existing genome/protein suites continue to pass unchanged.

## Files

- `apps/web/src/lib/network/types.ts`
- `apps/web/src/lib/network/model.ts`
- `apps/web/src/lib/network/normalize.ts`
- `apps/web/src/lib/network/filter.ts`
- `apps/web/src/lib/network/layout.ts`
- `apps/web/src/lib/network/viewport.ts`
- `apps/web/src/lib/network/geometry.ts`
- `apps/web/src/lib/network/labels.ts`
- `apps/web/src/lib/network/api.ts`
- `apps/web/src/lib/network/network.fixtures.ts`
- `apps/web/src/lib/network/useNetworkViewer.ts`
- `apps/web/src/components/network/NetworkViewer.tsx`
- `apps/web/src/app/visualization/NetworkDemo.tsx`
- `apps/web/src/app/visualization/page.tsx` (renders the demo)

## Validation

All commands green on the branch:

```shell
make lint        # biome + ruff
make typecheck   # pyright + tsc
make test        # web vitest + sdk-ts + api pytest
make build       # production web build
```
