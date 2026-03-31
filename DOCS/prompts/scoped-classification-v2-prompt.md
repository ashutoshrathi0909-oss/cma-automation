# Scoped Classification v2 — Backend Integration

## Context
You are integrating a new "Scoped Classification" engine into an existing CMA automation backend. The standalone prototype (`scoped_classifier.py` in project root) is already built and working. Your job is to wire it into the backend pipeline so it works end-to-end through the web app.

## The Problem Being Solved
The current AI classifier (Tier 2 in pipeline.py) gives Haiku ALL 131 CMA rows + ALL rules in one prompt. Haiku gets overwhelmed and hits an 87% ceiling. The scoped approach reduces this to ~6-15 rows per section, dramatically reducing cognitive load. Additionally, a multi-agent debate between two models catches errors that a single model misses.

## Architecture: Scoped Classification + Multi-Agent Debate

```
Extracted Line Item (with section, sheet_name)
         │
    Section Router
    (section_mapping.json → 23 categories)
         │
    Scoped Prompt Builder
    (for each section: only that section's CMA rows + CA rules + examples)
         │
    ┌────┴────┐
    ▼         ▼
DeepSeek R1  Gemini Flash 2.0    ← PARALLEL via OpenRouter
 (Thinker)    (Verifier)
    │         │
    └────┬────┘
    Agreement Check
    ┌────┴────┐
  AGREE     DISAGREE
    │         │
    ▼         ▼
Auto-approve  Debate Round (exchange reasoning, one more try)
              ┌────┴────┐
            AGREE     STILL DISAGREE
              │         │
              ▼         ▼
         Auto-approve  Flag as DOUBT
```

### Models (via OpenRouter)
- **DeepSeek R1** (`deepseek/deepseek-r1`) — "Thinker" role. Explicit chain-of-thought reasoning. ~$0.55/$2.19 per 1M tokens.
- **Gemini Flash 2.0** (`google/gemini-2.0-flash-001`) — "Verifier" role. Fast and cheap. ~$0.10/$0.40 per 1M tokens.
- Both called via OpenRouter API using the OpenAI-compatible endpoint.
- API key: `OPENROUTER_API_KEY` from .env

### Why Two Models
- Single model = unreliable confidence scores (model says 0.85 but is wrong)
- Two independent models agreeing = REAL confidence signal
- Two models disagreeing = genuine ambiguity → correct to flag as doubt
- Different model families (DeepSeek vs Google) = uncorrelated errors

## What Already Exists

### Standalone Prototype (REFERENCE — read this first)
- `scoped_classifier.py` — Complete working prototype with:
  - Section Router (3-tier: exact → keyword regex → sheet fallback)
  - Scoped Prompt Builder (pulls section-specific CMA rows + CA rules + examples)
  - SECTION_NORMALIZED_TO_CANONICAL mapping
  - KEYWORD_ROUTES patterns (30+ regex patterns)
  - Cost guards (token caps, item caps)
  - Analysis & reporting

### Ground Truth Data (used by the scoped prompt builder)
- `CMA_Ground_Truth_v1/reference/canonical_labels.json` — 131 CMA row definitions
- `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` — 385 CA expert rules
- `CMA_Ground_Truth_v1/database/training_data.json` — 1,326 training examples from 9 companies
- `CMA_Ground_Truth_v1/scripts/section_mapping.json` — 133 section → 23 categories
- `CMA_Ground_Truth_v1/scripts/sheet_name_mapping.json` — 46 sheet names → 6 source forms

### Current Pipeline (what you're modifying)
- `backend/app/services/classification/pipeline.py` — 3-tier orchestrator
  - Tier 0: RuleEngine (60 regex rules) — KEEP AS-IS
  - Tier 1: FuzzyMatcher (rapidfuzz against learned + reference mappings) — KEEP AS-IS
  - Tier 2: AIClassifier (`ai_classifier.py`) — REPLACE with Scoped Classifier + Debate
  - Tier 3: Doubt report — KEEP AS-IS
- `backend/app/services/classification/ai_classifier.py` — Current Haiku integration. THIS gets replaced.
- `backend/app/services/classification/rule_engine.py` — 60 regex rules (keep)
- `backend/app/services/classification/fuzzy_matcher.py` — Fuzzy matching (keep)
- `backend/app/services/classification/learning_system.py` — Learned mappings (keep)

### Docker Services
- `docker-compose.yml` — backend, frontend, worker, redis
- Worker runs classification tasks in `backend/app/workers/classification_tasks.py`

## What To Build

### Step 1: Create `backend/app/services/classification/scoped_classifier.py`
Port the standalone prototype into a proper backend service class:

1. **ScopedClassifier class** — initialized once, pre-loads all ground truth data:
   - Section mappings (from CMA_Ground_Truth_v1/scripts/)
   - Canonical labels (from CMA_Ground_Truth_v1/reference/)
   - CA rules (from CMA_Ground_Truth_v1/reference/)
   - Training examples (from CMA_Ground_Truth_v1/database/)
   - Pre-builds scoped contexts for all 23 sections
   - Section router (exact → keyword regex → sheet fallback) from prototype

2. **OpenRouter client** for calling DeepSeek R1 and Gemini Flash:
   - Use the `openai` Python package (OpenAI-compatible API, already in requirements.txt)
   - Base URL: `https://openrouter.ai/api/v1`
   - API key: `OPENROUTER_API_KEY` from settings/env
   - DeepSeek R1 model ID: `deepseek/deepseek-r1`
   - Gemini Flash model ID: `google/gemini-2.0-flash-001`
   - max_tokens: 200 per call
   - temperature: 0.0

3. **Debate protocol:**
   ```python
   async def classify(self, raw_text, section, sheet_name, industry_type, ...):
       # 1. Route to section
       section_norm = self.route_section(section, sheet_name)

       # 2. Build scoped prompt
       prompt = self.build_scoped_prompt(raw_text, section, sheet_name, section_norm, ...)

       # 3. Call both models in PARALLEL
       r1_result, flash_result = await asyncio.gather(
           self.call_deepseek(prompt),
           self.call_gemini(prompt),
       )

       # 4. Agreement check
       if r1_result.cma_row == flash_result.cma_row:
           return r1_result  # AGREE → high confidence, auto-approve

       # 5. Debate round: show each model the other's answer
       debate_prompt = f"{prompt}\n\nModel A chose Row {r1_result.cma_row}: {r1_result.reasoning}\nModel B chose Row {flash_result.cma_row}: {flash_result.reasoning}\nReconsider and pick the best answer."

       r1_v2, flash_v2 = await asyncio.gather(
           self.call_deepseek(debate_prompt),
           self.call_gemini(debate_prompt),
       )

       # 6. Second agreement check
       if r1_v2.cma_row == flash_v2.cma_row:
           return r1_v2  # AGREE after debate → medium confidence

       # 7. Still disagree → DOUBT
       return doubt_result(raw_text, r1_v2, flash_v2)
   ```

4. **Result format** — must return the same dict structure as current ai_classifier.py:
   ```python
   {
       "cma_field_name": str,
       "cma_row": int,
       "cma_sheet": str,  # "input_sheet"
       "broad_classification": str,
       "confidence": float,  # 0.95 if agreed first round, 0.85 if agreed after debate, 0.0 if doubt
       "is_doubt": bool,
       "doubt_reason": str | None,
       "reasoning": str,
       "alternatives": list,
   }
   ```

5. **Cost guards** (MANDATORY):
   - Hard cap: 500K total tokens per classification run
   - Max 300 items per document
   - No retry loops — if either API call fails, use the other model's answer alone. If both fail, flag as doubt.
   - Log token usage per item
   - Print running cost summary every 10 items in worker logs

### Step 2: Update `pipeline.py`
Replace the Tier 2 AI call:

```python
# Before (current):
self._ai = AIClassifier()
ai_result = self._ai.classify(...)

# After (scoped + debate):
self._scoped = ScopedClassifier()
ai_result = self._scoped.classify(...)
```

**Important:** The pipeline's classify_item method is synchronous but the debate protocol uses async (parallel API calls). You need to handle this — either:
- Make classify_item async and update the worker, OR
- Use `asyncio.run()` inside classify_item for the scoped classifier call, OR
- Use `concurrent.futures` for parallel calls instead of asyncio

Pick whatever integrates cleanest with the existing sync pipeline.

### Step 3: Mount Ground Truth Data in Docker
The ground truth files need to be accessible to the backend container.

In `docker-compose.yml`, add a read-only volume mount for the worker AND backend services:
```yaml
volumes:
  - ./CMA_Ground_Truth_v1:/app/CMA_Ground_Truth_v1:ro
```

The scoped classifier should resolve paths relative to this mount.

### Step 4: Config Updates
Add to `backend/app/config.py` (if not already there):
- `OPENROUTER_API_KEY` from env
- `CLASSIFIER_MODE` env var: "scoped" (new default) or "legacy" (old Haiku-only)
  - This allows falling back to the old classifier if needed

Add to `.env.example`:
```
CLASSIFIER_MODE=scoped
```

## Constraints

- **Use OpenRouter** for DeepSeek R1 and Gemini Flash via the openai Python package
- **Keep Tier 0 (rules) and Tier 1 (fuzzy) unchanged** — only replace Tier 2
- **Same output format** — classification dict must stay the same for DB insert, frontend, Excel generator
- **Pre-load ground truth once** — don't re-read JSON files for every item. Load at ScopedClassifier.__init__
- **Cost guards are not optional** — hard caps on tokens and items
- **No retry loops** — API failure on one model = use the other. Both fail = doubt.
- **Docker must work** — after changes, `docker compose up` must start clean
- **Add CLASSIFIER_MODE toggle** — so we can switch between scoped and legacy

## What NOT To Do
- Do NOT modify the frontend
- Do NOT modify the extraction pipeline
- Do NOT modify the Excel generator
- Do NOT run accuracy tests (testing is a separate session)
- Do NOT touch rule_engine.py or fuzzy_matcher.py
- Do NOT restructure the project layout beyond what's needed

## Verification Checklist
After integration:
1. `docker compose build` succeeds
2. `docker compose up` starts all services without errors
3. The scoped classifier loads ground truth data on init (check worker logs)
4. Both OpenRouter models are reachable (test with a single item)
5. Classification results have the same DB schema as before
6. `CLASSIFIER_MODE=legacy` falls back to old Haiku classifier
7. Cost tracking appears in worker logs

## File Structure After Changes
```
backend/app/services/classification/
├── pipeline.py              ← Modified: uses ScopedClassifier for Tier 2
├── scoped_classifier.py     ← NEW: scoped classification + debate engine
├── ai_classifier.py         ← Kept: used when CLASSIFIER_MODE=legacy
├── rule_engine.py           ← Unchanged
├── fuzzy_matcher.py         ← Unchanged
└── learning_system.py       ← Unchanged
```
