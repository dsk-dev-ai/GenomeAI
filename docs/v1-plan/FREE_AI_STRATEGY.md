# V1 Free AI Strategy

**Rule:** V1 uses ZERO paid AI. Every AI feature must work on free tiers only.

---

## Provider Fallback Chain

```
Priority 1: Ollama (Local)
  ↓ if unavailable or model too small
Priority 2: Google Gemini Free (250 req/day)
  ↓ if quota exhausted (HTTP 429)
Priority 3: OpenRouter Free (50-1000 req/day)
  ↓ if quota exhausted
Priority 4: Groq Free (1000-14400 req/day)
  ↓ if quota exhausted
Priority 5: Mistral Free (~1B tokens/month)
  ↓ if all exhausted
Fallback: Queue request, retry when quota resets
```

---

## Provider Details

### 1. Ollama (Local) — Primary

| Detail | Value |
|--------|-------|
| Endpoint | `http://localhost:11434/v1` |
| Auth | None (API key: "ollama") |
| Rate limit | Unlimited |
| Function calling | Yes |
| Context window | Depends on model (8K-128K) |

**Recommended models:**
- `qwen3.5:14b` — General reasoning (~10GB VRAM)
- `deepseek-r1:32b` — Deep reasoning (~20GB VRAM)
- `qwen2.5-coder:32b` — Code/data analysis (~20GB VRAM)
- `llama3.3:70b` — Frontier quality (~48GB VRAM)

**Setup:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3.5:14b
```

### 2. Google Gemini Free — Best Cloud Free

| Detail | Value |
|--------|-------|
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Auth | API key (free from Google AI Studio) |
| Rate limit | 250 req/day (Flash), 1000 req/day (Flash-Lite) |
| Context | 1M tokens |
| Function calling | Yes |

**Free models:**
- Gemini 2.5 Flash (best quality)
- Gemini 2.0 Flash (stable)
- Gemini 2.5 Flash-Lite (highest daily limit)

**Detection:** HTTP 429 on quota exhaustion.

### 3. OpenRouter Free — Multi-Model Gateway

| Detail | Value |
|--------|-------|
| Endpoint | `https://openrouter.ai/api/v1` |
| Auth | API key (free from openrouter.ai) |
| Rate limit | 50 req/day (no credits) → 1000 req/day ($10 purchase) |
| Function calling | Yes (model-dependent) |

**Free models (rotate):**
- `meta-llama/llama-4-maverick:free` (1M context)
- `openai/gpt-oss-120b:free` (131K context)
- `nvidia/nemotron-3-ultra:free` (1M context)
- `google/gemma-4-31b:free` (262K context)

**Detection:** Response headers `X-RateLimit-Remaining`.

### 4. Groq Free — Fastest Inference

| Detail | Value |
|--------|-------|
| Endpoint | `https://api.groq.com/openai/v1` |
| Auth | API key (free from console.groq.com) |
| Rate limit | 30 RPM, 1000-14400 RPD |
| Speed | ~3000 tok/s |
| Function calling | Yes |

**Free models:**
- `llama-3.1-8b-instant` (14400 RPD)
- `llama-3.3-70b-versatile` (1000 RPD)
- `qwen/qwen3-32b` (1000 RPD)

### 5. Mistral Free — Highest Monthly Budget

| Detail | Value |
|--------|-------|
| Endpoint | `https://api.mistral.ai/v1` |
| Auth | API key (free from console.mistral.ai) |
| Rate limit | ~1B tokens/month |
| Function calling | Yes |

**Free models:**
- Mistral Large
- Mistral Medium
- Mistral Small
- Codestral

---

## Implementation

```python
class AIGateway:
    providers = [
        OllamaProvider(),     # Priority 1: local, unlimited
        GeminiProvider(),     # Priority 2: 250 req/day
        OpenRouterProvider(), # Priority 3: 50-1000 req/day
        GroqProvider(),       # Priority 4: 1000-14400 req/day
        MistralProvider(),    # Priority 5: ~1B tokens/month
    ]

    async def complete(self, prompt, **kwargs):
        for provider in self.providers:
            if provider.has_quota():
                try:
                    return await provider.complete(prompt, **kwargs)
                except (RateLimitError, ServiceUnavailable):
                    continue
        # All providers exhausted — queue for later
        raise AllProvidersExhausted()
```

---

## Daily Capacity Summary

| Provider | Requests/Day | Tokens/Day (est.) |
|----------|-------------|-------------------|
| Ollama | Unlimited | Unlimited |
| Gemini | 250 | ~250K |
| OpenRouter | 50-1000 | ~500K |
| Groq | 1000-14400 | ~5M |
| Mistral | ~33K | ~1B tokens/month |
| **Total** | **~35K+** | **~6M+ tokens/day** |

This is MORE than enough for a genomics research platform.
