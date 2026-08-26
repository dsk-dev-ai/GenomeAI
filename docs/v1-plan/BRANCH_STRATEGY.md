# V1 Branch Strategy

Each phase and sub-phase gets its own branch. Work is sequential: complete one, merge, then start next.

---

## Branch Naming

```
v1/<phase>.<sub-phase>/<short-description>

Examples:
v1/1.3/protein-domain
v1/2.1/ncbi-eutils-core
v1/4.2/ollama-provider
v1/8.6/summarization
```

---

## Workflow Per Sub-Phase

```
1. Create branch from main
   git checkout main && git pull
   git checkout -b v1/1.3/protein-domain

2. Implement (models, repo, service, API, tests)

3. Validate
   make lint
   make typecheck
   make test

4. Commit
   git add .
   git commit -m "feat(domain): add protein domain"

5. Push and create PR
   git push origin v1/1.3/protein-domain
   gh pr create

6. Merge to main (after review)

7. Pull latest
   git checkout main && git pull

8. Start next sub-phase
```

---

## Rules

1. **One sub-phase per branch** — keep PRs small and focused
2. **Always validate before merge** — lint, typecheck, tests must pass
3. **Merge to main before next branch** — each sub-phase builds on previous
4. **No skipping** — complete sub-phases in order within a phase
5. **Phases can parallelize** — V1.1 and V1.3 can run simultaneously (different concerns)
6. **Document as you go** — each connector gets a doc page

---

## Phase Dependencies

```
V1.1 (Core Domains) ──→ V1.2 (Connectors) ──→ V1.7 (Data Integration)
                                        │
                                        ├──→ V1.5 (Search)
                                        │
                                        ├──→ V1.8 (Literature)
                                        │
                                        ├──→ V1.9 (Drugs)
                                        │
                                        └──→ V1.10 (Variant Interpretation)

V1.4 (AI Gateway) ──→ V1.8, V1.9, V1.10, V1.11 (all AI-powered features)

V1.3 (Workflow) ── already done
V1.6 (Visualization) ── already done

V1.11 (Reports) ──→ V1.12 (Testing & Quality)
```

---

## PR Template

```markdown
## V1 Sub-phase: [phase.sub-phase] [description]

### What this PR adds
- [ ] Feature 1
- [ ] Feature 2

### Files changed
- apps/api/src/genomeai_api/domains/...
- apps/api/tests/test_...

### Verification
- [ ] make lint passes
- [ ] make typecheck passes
- [ ] make test passes (X tests)
- [ ] Documentation updated

### V1 Progress
- [ ] V1.1 Core Domains
- [ ] V1.2 Database Connectors
- [ ] V1.4 AI Gateway
- [ ] V1.5 Search
- [ ] V1.7 Data Integration
- [ ] V1.8 Literature
- [ ] V1.9 Drugs
- [ ] V1.10 Variant Interpretation
- [ ] V1.11 Reports
- [ ] V1.12 Testing
```
