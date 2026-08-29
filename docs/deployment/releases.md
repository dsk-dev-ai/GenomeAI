# Releases & Deployment Guide

How the automatic release → deploy pipeline works, what triggers it, and how to
operate it.

## Pipeline

```
GitHub Release (tag v1.0.0 on main)
        │
        ▼
.github/workflows/release-deploy.yml   "Deploy Release (Live Demo)"
  checkout tag → install (pnpm + uv) → lint/format → typecheck →
  tests → build web → deploy backend (Render hook) → deploy frontend
  (Vercel --prod) → wait for backend /health → wait for frontend →
  real API smoke test → UI smoke test → comment on the release
        │
        ▼
  Live Demo updated: https://<project>.vercel.app  +  https://genomeai-api.onrender.com
```

Only the **CI workflow** gate applies to normal PRs/pushes. The **deploy
workflow** runs on version tags and reports failure loudly if any step fails
(a broken build is never deployed: build + tests run before deployment, and
health checks must pass after it).

## What triggers deployment

Creating a GitHub Release against the `main` branch with a tag matching `v*`
(e.g. `v1.0.0`, `v1.1.0`, `v2.0.0`) triggers deployment automatically.

- **Do:** merge the release PR to `main` first, then create the Release with
  the tag on the `main` branch. The tag must point at the main branch head so
  the deployed code equals the released code.
- **Manual rerun:** `Actions` → *Deploy Release (Live Demo)* → *Run workflow*.

`docs/deployment/architecture.md` explains the hosting topology.

## Where the public URLs come from

- **Frontend:** Vercel assigns `https://<project>.vercel.app` when you import
  the repo (`apps/web`). Set it as the `GENOMEAI_FRONTEND_URL` variable.
- **Backend:** Render assigns `https://<service>.onrender.com` when you create
  the web service from `render.yaml`. Set it as `GENOMEAI_BACKEND_URL`.

## Required GitHub Secrets and Variables

Repository → Settings → Secrets and variables → Actions.

| Kind | Name | Example / source |
|------|------|------------------|
| Secret | `VERCEL_TOKEN` | Vercel → Settings → Tokens |
| Secret | `VERCEL_ORG_ID` | `~/.vercel/project.json` (`orgId`) |
| Secret | `VERCEL_PROJECT_ID` | `~/.vercel/project.json` (`projectId`) |
| Secret | `RENDER_DEPLOY_HOOK_URL` | Render service → Settings → Deploy Hook |
| Variable | `GENOMEAI_FRONTEND_URL` | `https://<project>.vercel.app` |
| Variable | `GENOMEAI_BACKEND_URL` | `https://genomeai-api.onrender.com` |

Optional: `VERCEL_GENOMEAI_API_URL` (Secret) overrides the backend URL on the
continuous Vercel deploy; `GEMINI_API_KEY`/`GOOGLE_API_KEY` (Render env) enable
AI features (the API falls back to basic analysis without a key).

Keep the token permissions at least-privilege (only the repos/projects above).

## How a maintainer creates a new version

1. Work on a branch, open a PR → CI must be green (Lint, Type Check, Test).
2. Merge to `main`.
3. Update `CHANGELOG.md` (Keep a Changelog) with the new version.
4. Create a GitHub Release with tag `v1.0.0` (or bump per Semantic Versioning)
   pointing at `main` → deployment runs automatically.
5. Confirm the workflow completed and the release comment says deploy succeeded.

## How to run locally

See `README.md` → Quick Start (`pnpm dev`, `uvicorn`, optional `docker compose
up` for Postgres/Redis).

## What happens when deployment fails

The workflow marks the run (and the release) as failed and comments on the
release. The previous deployed version stays live (Vercel/Render do not remove
the previous deploy). Common causes:

- A secret/variable is missing → the workflow fails with a clear message.
- Backend did not pass `/health` within 16 minutes (Render Docker cold build)
- Frontend not reachable within 11 minutes (Vercel build)
- Real API / UI smoke test failed (third-party biomedical API outage is
  retried 3× before failing)

Fix the cause and re-run the workflow (`workflow_dispatch`) or create a new
Release.