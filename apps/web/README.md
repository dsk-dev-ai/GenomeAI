# `apps/web` — Web Application

GenomeAI web dashboard and user interface.

## Technology

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS v3
- **Runtime:** Node.js 24+

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Home page — project introduction |
| `/health` | Health check status page |
| `/*` | 404 catch-all page |

## Entry Point

- Development: `pnpm --filter @genomeai/web dev`
- Build: `pnpm --filter @genomeai/web build`

## Future Responsibilities

- Pipeline management dashboard
- Data exploration and visualization
- Analysis monitoring
- User preferences and settings
