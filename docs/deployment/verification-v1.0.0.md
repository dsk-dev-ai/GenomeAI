# V1.0.0 Live Demo Verification

Verified against the public stack on 2026-08-29 after tagging `v1.0.0`.

## Public endpoints

- Frontend: https://genomeai.vercel.app — HTTP 200, renders
  `<title>GenomeAI — Open-source intelligence for the genome era</title>`
- Backend: https://genomeai-api.onrender.com — `/health` returns `{"status":"ok"}`

## Real API smoke test (live)

`POST https://genomeai-api.onrender.com/api/v1/genes/analyze`
with `{"symbol":"BRCA1"}` returned HTTP 200 with:

| Field | Value |
|-------|-------|
| `source` | `ncbi+ollama` (AI + public-data pipeline) |
| `name` | `BRCA1 DNA repair associated` |
| `function` | populated (287 chars) |
| `summary` | populated (382 chars) |
| `key_variants` | 4 entries |
| `associated_diseases` | 6 entries |
| `drug_targets` | 5 entries |

Second gene `TP53` also returned populated AI fields.

## Release pipeline

- Tag `v1.0.0` on `main` triggered `.github/workflows/release-deploy.yml`.
- All jobs passed: install, lint/format, type check, tests, `pnpm turbo build`,
  Render deploy (deploy hook), Vercel production deploy (REST API), backend
  `/health` wait, frontend reachability wait, real-API smoke test, UI smoke
  test, release status comment.
- Live Demo auto-updates on every release tag; main-branch merges deploy via
  the Vercel GitHub integration.

## Free-tier notes (expected behavior, not faults)

- Render free instance spins down after ~15 min idle; first request triggers a
  cold start (~30–60 s) and may return 502 until warm.
- Free instance has 0.1 CPU / 512 MB RAM; intermittent 502s or OOM restarts can
  occur under heavy load. The API degrades gracefully (basic analysis fallback)
  without Redis/Postgres.

## Deploy credentials

All secrets live in GitHub Actions Secrets / Vercel project / Render system env
— never committed. See `docs/deployment/releases.md`.