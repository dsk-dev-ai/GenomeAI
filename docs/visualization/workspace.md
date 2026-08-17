# Integrated Research Workspace (Phase 6.9)

Assembles the Phase 6.2–6.8 visualization capabilities into one coherent
research UI at **`/visualization/workspace`** (linked from `/visualization`).
The workspace gives a researcher related genomic and scientific views side by
side, driven by a shared research context.

## Scope

The workspace reuses the existing visualization platform — it **re-renders**
the shipped `GenomeBrowser`, `GeneTranscriptViewer`, `NetworkViewer`,
`ProteinViewer`, and the scientific chart components; it does **not** duplicate
or re-implement any rendering logic. New code is limited to workspace
composition: context state, a data-source seam, thin panels, layout, and
docs/tests.

- No C++, WebAssembly, WebGPU, Three.js, Cytoscape.js, D3.js, or another
  rendering architecture.
- No new runtime dependencies.
- Phase 5 search/backend functionality is untouched.
- The Phase 6.1 `useVisualizationData` lifecycle remains the data authority;
  every panel loads through it (directly or via its existing domain hook).

## Route and layout

| Entry | Purpose |
|-------|---------|
| `apps/web/src/app/visualization/workspace/page.tsx` | Server component: heading, description, `<ResearchWorkspace />` |
| `apps/web/src/app/visualization/page.tsx` | Adds a navigation link to the workspace |

The workspace renders a responsive panel grid:

```
┌──────────────────────────────────────────────┐
│ Research context selector                    │
├──────────────────────────────────────────────┤
│ Genome Browser            (full width)       │
├───────────────┬──────────────────────────────┤
│ Gene/Transcript│ Biological Network Viewer   │
├───────────────┼──────────────────────────────┤
│ Protein Viewer│ Expression Chart             │
├───────────────┼──────────────────────────────┤
│ Expression    │ Volcano Plot                 │
│ Heatmap       │                              │
├───────────────┼──────────────────────────────┤
│ Coverage Chart│ Distribution Chart           │
└───────────────┴──────────────────────────────┘
```

Panels stack to a single column below `lg`, so the workspace stays usable on
smaller screens.

## Architecture

### Files

| File | Responsibility |
|------|----------------|
| `lib/workspace/researchContext.ts` | `ResearchContext` type, preset contexts (TP53 / BRCA1 loci), `contextRegionKey`, `customContextFromInterval`, `regionToViewport` |
| `lib/workspace/dataSources.ts` | `WorkspaceDataSource` interface (pure seam) + `resolveFixture` loader helper |
| `components/workspace/fixtureDataSources.ts` | `fixtureWorkspaceDataSource`: the default demo provider backed by the Phase 6 dev fixtures |
| `components/workspace/ResearchWorkspace.tsx` | Owns the active context + custom contexts, renders the selector and the panel grid |
| `components/workspace/ResearchContextSelector.tsx` | Preset `<select>` + custom region form (shared Phase 6.2 region parser) |
| `components/workspace/GenomeBrowserPanel.tsx` | Wires the Phase 6.2 `GenomeBrowser` with region-scoped gene + variant tracks |
| `components/workspace/GeneTranscriptPanel.tsx` | Loads the gene overlapping the region and renders the Phase 6.3 `GeneTranscriptViewer` |
| `components/workspace/NetworkPanel.tsx` | `useNetworkViewer` + `NetworkViewer` (Phase 6.6) |
| `components/workspace/ProteinPanel.tsx` | `useProteinViewer` + `ProteinViewer` (Phase 6.5) |
| `components/workspace/AnalysisChartPanels.tsx` | `ExpressionPanel`, `HeatmapPanel`, `VolcanoPanel`, `CoveragePanel`, `DistributionPanel` (Phase 6.7 / 6.8 hooks + components) |

### Data flow

```
ResearchWorkspace ── activeContext (ResearchContext)
      │  region
      ├──▶ GenomeBrowserPanel  (key = contextRegionKey)  ──▶ GenomeBrowser tracks
      ├──▶ GeneTranscriptPanel (key = contextRegionKey)  ──▶ useVisualizationData ──▶ GeneTranscriptViewer
      └──▶ NetworkPanel / ProteinPanel / *ChartPanels  ──▶ existing domain hooks
                │
                └── dataSource: WorkspaceDataSource (default: fixtureWorkspaceDataSource)
```

- **Region-driven panels** (Genome Browser, Gene / Transcript viewer) are
  remounted with `key={contextRegionKey(activeContext.region)}` whenever the
  context region changes, so they always open on the shared region. Because
  `GenomeBrowser` owns its viewport internally, remounting is the only
  supported way to move it to a new region; within a context the user keeps
  full zoom/pan control.
- **Whole-dataset panels** (network, protein, all charts) keep their own local
  state (viewport, filters, selections) across context changes — panel state
  stays local and predictable.

### Panel responsibilities

| Panel | Module | Context-driven? | State |
|-------|--------|-----------------|-------|
| Genome Browser | Phase 6.2 | Yes (region) | Browser viewport (local) |
| Gene / Transcript | Phase 6.3 | Yes (region) | Transcript selection (local) |
| Biological Network | Phase 6.6 | No | Layout, viewport, filter, selection |
| Protein Viewer | Phase 6.5 | No | Residue window, feature selection |
| Expression / Heatmap / Volcano / Coverage / Distribution | Phase 6.7/6.8 | No | Chart state (local) |

## API usage

The workspace does not invent endpoints. It reuses the existing typed
adapters as the production path and the existing dev fixtures for the demo:

- **Genome / variant** region queries: `fetchGeneTranscripts`,
  `fetchIntervalFeatures`, `fetchVariants` (Phase 5 `POST /search/{domain}/coordinate`)
- **Network**: `fetchNetworkGraph` (`GET /networks/{id}`, not yet implemented in
  the backend)
- **Protein**: `fetchProtein` (`GET /proteins/{id}`)
- **Expression / advanced charts**: `fetchExpressionDataset`,
  `fetchHeatmapDataset`, `fetchVolcanoDataset`, `fetchCoverageDataset`,
  `fetchDistributionDataset` (endpoints not yet implemented in the backend)

`WorkspaceDataSource` is a pure seam: `fixtureWorkspaceDataSource` implements
it with fixtures for the demo; a production deployment swaps the provider for
the adapters above **without touching the workspace UI**. Region parsing in the
selector reuses `parseGenomeRegion` / `formatRegionLabel` from
`lib/genome/region.ts` / `lib/genome/geometry.ts`.

## Fixture boundary

The default provider is backed entirely by the isolated Phase 6 dev fixtures
(`genomeBrowser.fixtures`, `geneTranscript.fixtures`, `network.fixtures`,
`protein.fixtures`, `scientific/advanced.fixtures`, `scientific/expression.fixtures`),
consistent with the 6.2–6.8 demos. The network, protein, and analysis chart
datasets are **TP53-pathway fixtures** and are not region-queryable, so those
panels render the same analysis for every context. This is a documented
limitation, not silent backend scope: the panels are wired so a real
region-queryable endpoint can be dropped in later.

## Loading, empty, and error states

Every panel routes through the shared lifecycle (`useVisualizationData` /
`useChartData`):

- **Loading**: `VisualizationContainer` shows an accessible loading label
  (e.g. "Loading gene structure...", "Loading network...").
- **Empty**: a custom region with no fixture gene shows
  "No gene structure to show in this region."; genome tracks show their own
  per-track empty messages; charts show their standard empty messages.
- **Error**: `VisualizationErrorState` renders a `role="alert"` panel with a
  keyboard-accessible **Retry** button wired to `refetch`.
- Workspace tests inject empty/failing loaders through `WorkspaceDataSource`
  to verify these states deterministically.

## Accessibility

- Headings: the route uses an `<h1>`; every panel title is an `<h2>` inside a
  labeled `<section>` (`VisualizationContainer`'s `aria-labelledby`).
- Context selector: a labeled `<select>` ("Research context"), a labeled
  region input ("Go to region"), real submit buttons, a `role="alert"`
  region-parse error, and an `aria-live="polite"` output announcing the active
  region.
- Existing panel accessibility (keyboard-selectable marks, `aria-pressed`,
  Enter/Space, focus rings, readable detail panels) is preserved unchanged
  because the components are reused as-is.
- The Genome Browser's navigation controls and region form remain fully
  keyboard operable.

## Tests

`apps/web` vitest tests added for Phase 6.9:

| File | Coverage |
|------|----------|
| `lib/workspace/researchContext.test.ts` | preset contexts, id lookup, region→viewport, region key, custom context |
| `lib/workspace/dataSources.test.ts` | `resolveFixture` contract (resolve / abort / no cache) |
| `components/workspace/fixtureDataSources.test.ts` | interval filtering, abort handling, fixture resolution for every loader |
| `components/workspace/ResearchContextSelector.test.tsx` | labeled select, aria-live output, preset change, valid/invalid custom region, alert |
| `components/workspace/ResearchWorkspace.test.tsx` | panel rendering, context→browser sync, custom-region navigation, gene empty state, panel error + retry, loading state, whole-dataset panel independence, controls a11y |

Phase 6.11 added the loading-state, panel error, and context-change
independence tests (30 workspace tests today). Existing tests are unchanged;
the full suite must stay green (see `Makefile` targets `lint` / `typecheck` /
`test` / `build`).

## Limitations

- The Genome Browser and Gene / Transcript viewer only react to context
  changes at the workspace level (via remount); intra-browser navigation does
  not propagate back to the workspace context.
- Relationship and analysis panels are TP53-pathway fixtures and do not
  change with the context region (fixture boundary above).
- The backend does not yet expose network, protein-feature, expression, or
  advanced-chart endpoints; the workspace documents these contracts via the
  existing typed adapters rather than creating backend scope.