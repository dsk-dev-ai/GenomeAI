# Deployment Architecture

This document describes how GenomeAI is deployed to public, free hosts so that
any visitor to the GitHub repository can open and use the live demo.

## Overview

GenomeAI is a monorepo with two runtime components:

```
┌────────────────────┐         ┌─────────────────────┐
│  Frontend          │  HTTP   │  Backend            │
│  Next.js 15        │ ──────▶ │  FastAPI (uvicorn)  │
│  Vercel (free)     │         │  Render (free)      │
│  *.vercel.app      │         │  *.onrender.com     │
└────────────────────┘         └─────────────────────┘
```

The frontend calls the backend over HTTPS using `NEXT_PUBLIC_GENOMEAI_API_URL`
(embed at build time). The backend talks to public biomedical APIs (NCBI,
ChEMBL, Reactome, ...) and optionally a Gemini/OpenRouter AI provider.

Because this project has a **server-rendered Next.js frontend and a Python
FastAPI backend**, GitHub Pages (static only) is NOT used. Both services run on
real free-tier hosts that support the required runtimes.

## Free-tier hosts

### Frontend — Vercel (free)

- Public URL: `https://<project>.vercel.app`
- Deployed by the Vercel GitHub integration (push to main / PR preview) and, for
  releases, by a GitHub Actions step that triggers a deploy via the Vercel
  REST API (`POST /v13/deployments`)
- Build command from `apps/web/package.json` (Next.js)
- Free-tier limitations:
  - Serverless, non-commercial usage only
  - Build minutes and bandwidth quotas apply
  - No database (Postgres) or long-lived processes

### Backend — Render (free)

- Public URL: `https://genomeai-api.onrender.com` (or your chosen name)
- Docker web service built from `Dockerfile.api` (uv-managed workspace)
- Free-tier limitations:
  - Spins down after ~15 minutes of inactivity → first request after idle
    triggers a **cold start** (~30–60 s). The release workflow waits for this.
  - 750 instance hours/month
  - Free Postgres (if used later) expires after 90 days — the V1 demo does
    **not** require Postgres/Redis (the API degrades gracefully), so the
    single free service is sufficient.

## Environment variables / secrets

See `docs/deployment/releases.md` for the full list and how to set them.

| Variable | Where | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_GENOMEAI_API_URL` | Vercel build env | Public backend URL the browser uses |
| `GENOMEAI_CORS_ORIGINS` | Render env | Allowed browser origins (defaults in API) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Render env | Optional AI provider key (graceful fallback) |

Secrets are never committed. All deploy credentials live in GitHub Actions
Secrets / Variables. See `SECURITY.md`.