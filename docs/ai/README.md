# AI/ML Documentation

The live AI implementation is documented across the repo:

- AI providers (Gemini default, Ollama local): `apps/api/src/genomeai_api/ai/`
- AI analysis services (gene, protein, variant, drug, pathway, disease,
  literature, report): see [`ROADMAP.md`](../../ROADMAP.md) Phase 8 and
  [`apps/api/services/`](../../apps/api/src/genomeai_api/services/)
- AI gateway design: [`../decisions/`](../decisions/) and
  [`../v1-plan/FREE_AI_STRATEGY.md`](../v1-plan/FREE_AI_STRATEGY.md) (historical)

Planned future documents (ML serving layer, when built):

| Document | Description |
|----------|-------------|
| `models.md` | Supported model architectures and model registry |
| `training.md` | Training pipeline configuration and distributed training |
| `inference.md` | Inference serving, batching, and caching |
| `explainability.md` | Model interpretability and explainability methods |