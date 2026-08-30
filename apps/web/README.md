# `apps/web` — Web Application

GenomeAI web dashboard and user interface — the live demo at
<https://genomeai.vercel.app>.

## Technology

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS v3
- **Runtime:** Node.js 20+

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Home page — live demo landing |
| `/health` | Health check status page |
| `/research` | Multi-domain research dashboard |
| `/research/gene` | Gene analysis |
| `/research/protein` | Protein analysis |
| `/research/variant` | Variant interpretation |
| `/research/drug` | Drug–target analysis |
| `/research/pathway` | Pathway analysis |
| `/research/disease` | Disease association |
| `/research/literature` | Literature search |
| `/research/report` | Multi-domain report |
| `/visualization` | Visualization foundation demo (Phase 6.1) |
| `/*` | 404 catch-all page |

## Entry Point

- Development: `pnpm --filter @genomeai/web dev`
- Build: `pnpm --filter @genomeai/web build`

## Testing

- Unit tests: `pnpm --filter @genomeai/web test` (Vitest + Testing Library)
- Tests live alongside the code as `*.test.ts(x)`. See
  [Visualization Architecture](../../docs/visualization/architecture.md) for
  coverage details and conventions.