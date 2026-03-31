# FIX: Scoped Classification v2 — Replace Haiku with DeepSeek V3 + Gemini Flash Debate

> **STATUS: COMPLETED** — All changes below have been applied and tested. This document is retained as an architecture reference.
>
> **Post-integration bugs found and fixed (4):**
> 1. **`classify_sync` crash in ARQ workers** — `asyncio.get_event_loop()` fails in worker threads (no running loop). Fixed by using `asyncio.new_event_loop()` instead.
> 2. **GET /api/documents/{id} missing** — Endpoint returned 405 (only DELETE existed). Added proper GET handler.
> 3. **Row offset in canonical_labels.json** — All `sheet_row` values were off by -1 vs the CMA Excel template. Bumped every row +1 (e.g., "Domestic Sales" 21 → 22).
> 4. **Ground truth path resolution** — `parents[4]` was wrong for Docker mount layout. Changed to `parents[3]`.
> 5. **pipeline.py hardcoded method** — Lines 191 and 217 had `"ai_haiku"` hardcoded instead of using `ai_result.classification_method`. Fixed.

> **Model:** Sonnet | **Effort:** High | **Scope:** Backend only — DO NOT touch frontend, extraction, or Excel

## The Problem

The current `backend/app/services/classification/scoped_classifier.py` was built WRONG. It uses:
- **Anthropic Haiku** via `anthropic` Python package (user has NO Anthropic credits — calls WILL fail)
- **Single model** — no multi-agent debate
- classification_method hardcoded as `"ai_haiku_scoped"` but `pipeline.py` line 191 overrides it with `"ai_haiku"` anyway

**What it SHOULD use:**
- **DeepSeek V3** (`deepseek/deepseek-chat`) + **Gemini Flash 2.0** (`google/gemini-2.0-flash-001`)
- Both via **OpenRouter** using the `openai` Python package (OpenAI-compatible API)
- **Multi-agent debate protocol** (parallel calls → agreement check → debate round → doubt if still disagree)
- API key: `OPENROUTER_API_KEY` from environment (already in `.env`)

## What You MUST Read First

1. `backend/app/services/classification/scoped_classifier.py` — the file you're rewriting (567 lines)
2. `DOCS/prompts/scoped-classification-v2-prompt.md` — the CORRECT architecture spec (read ALL of it)
3. `backend/app/services/classification/ai_classifier.py` — reference for `AIClassificationResult` dataclass and OpenRouter OpenAI client usage
4. `backend/app/services/classification/pipeline.py` — the caller (you must fix the hardcoded `"ai_haiku"` strings too)
5. `backend/app/config.py` — config (needs `CLASSIFIER_MODE` setting)

## Architecture: Multi-Agent Debate Protocol

```
Extracted Line Item (raw_text, section, amount)
         │
    Section Router (KEEP AS-IS — already working)
    (section_mapping.json → 23 categories)
         │
    Scoped Prompt Builder (KEEP AS-IS — already working)
    (for each section: only that section's CMA rows + CA rules + examples)
         │
    ┌────┴────┐
    ▼         ▼
DeepSeek V3  Gemini Flash 2.0    ← PARALLEL via OpenRouter (openai package)
(Classifier)  (Verifier)
    │         │
    └────┬────┘
    Agreement Check
    ┌────┴────┐
  AGREE     DISAGREE
    │         │
    ▼         ▼
Auto-approve  Debate Round (exchange reasoning, one more try)
(conf=0.95)   ┌────┴────┐
            AGREE     STILL DISAGREE
              │         │
              ▼         ▼
         Auto-approve  Flag as DOUBT
         (conf=0.85)   (conf=0.0)
```

## Exact Changes Required

### File 1: `backend/app/services/classification/scoped_classifier.py` — REWRITE

**What to KEEP from the current file (copy these exactly):**
- All imports except `anthropic` (replace with `openai`)
- `SECTION_NORMALIZED_TO_CANONICAL` dict (lines 53-142)
- `_SECTION_TO_BROAD` dict (lines 145-169)
- `_KEYWORD_ROUTES` list (lines 172-199)
- `_ScopedContext` dataclass (lines 240-246)
- All data loading methods: `_load_section_mapping`, `_load_sheet_mapping`, `_load_canonical_labels`, `_load_rules`, `_load_training_data` (lines 488-513)
- `_build_scoped_contexts` method (lines 517-566)
- `_route_section` method (lines 344-373)
- `_build_prompt` method (lines 377-420) — but see prompt modification below

**What to REMOVE:**
- `from anthropic import Anthropic, RateLimitError`
- `ANTHROPIC_HAIKU_MODEL` constant
- `_SCOPED_TOOL_SCHEMA` — not needed for OpenRouter (use plain JSON parsing)
- `self._client = Anthropic(api_key=settings.anthropic_api_key)`
- The entire `classify()` method (replace with debate version)
- The `_parse_response()` method (replace)
- Rate limit retry logic (no retry loops — see constraints)

**What to ADD:**

#### 1. OpenRouter Client (use openai package)
```python
from openai import OpenAI

# Models
DEEPSEEK_V3_MODEL = "deepseek/deepseek-chat"
GEMINI_FLASH_MODEL = "google/gemini-2.0-flash-001"

# In __init__:
settings = get_settings()
self._openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)
```

#### 2. Async Debate Protocol
The classify method MUST be async because it calls two models in parallel:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for parallel API calls
_executor = ThreadPoolExecutor(max_workers=4)

async def classify(self, raw_text, amount, section, industry_type, document_type, fuzzy_candidates) -> AIClassificationResult:
    sec_norm = self._route_section(section or "", document_type)
    context = self._contexts.get(sec_norm) or self._contexts["admin_expense"]
    prompt = self._build_prompt(raw_text, amount, section or "not specified", context)

    # Round 1: Call both models in PARALLEL
    loop = asyncio.get_event_loop()
    try:
        v3_future = loop.run_in_executor(_executor, self._call_model, DEEPSEEK_V3_MODEL, prompt)
        flash_future = loop.run_in_executor(_executor, self._call_model, GEMINI_FLASH_MODEL, prompt)
        v3_result, flash_result = await asyncio.gather(v3_future, flash_future, return_exceptions=True)
    except Exception as e:
        logger.error("Both model calls failed: %s", e)
        return self._make_doubt("Both AI models failed")

    # Handle individual model failures
    if isinstance(v3_result, Exception) and isinstance(flash_result, Exception):
        return self._make_doubt("Both AI models failed")
    if isinstance(v3_result, Exception):
        v3_result = None
    if isinstance(flash_result, Exception):
        flash_result = None

    # If only one model responded, use its answer (with lower confidence)
    if v3_result is None:
        return self._single_model_result(flash_result, context, method="scoped_single_gemini")
    if flash_result is None:
        return self._single_model_result(v3_result, context, method="scoped_single_deepseek")

    # Round 1 Agreement Check
    if v3_result["cma_row"] == flash_result["cma_row"]:
        logger.info("AGREE round 1: row %d for '%s'", v3_result["cma_row"], raw_text[:50])
        return self._agreed_result(v3_result, context, confidence=0.95, method="scoped_agree")

    # DISAGREE → Debate Round
    logger.info("DISAGREE: V3=%d vs Flash=%d for '%s'", v3_result["cma_row"], flash_result["cma_row"], raw_text[:50])
    debate_prompt = self._build_debate_prompt(prompt, v3_result, flash_result)

    try:
        v3_v2_future = loop.run_in_executor(_executor, self._call_model, DEEPSEEK_V3_MODEL, debate_prompt)
        flash_v2_future = loop.run_in_executor(_executor, self._call_model, GEMINI_FLASH_MODEL, debate_prompt)
        v3_v2, flash_v2 = await asyncio.gather(v3_v2_future, flash_v2_future, return_exceptions=True)
    except Exception:
        # Debate failed — use round 1 majority or doubt
        return self._make_doubt(f"Debate failed. V3={v3_result['cma_row']}, Flash={flash_result['cma_row']}")

    # Handle debate failures
    if isinstance(v3_v2, Exception): v3_v2 = v3_result  # fall back to round 1
    if isinstance(flash_v2, Exception): flash_v2 = flash_result

    # Round 2 Agreement Check
    if v3_v2["cma_row"] == flash_v2["cma_row"]:
        logger.info("AGREE after debate: row %d for '%s'", v3_v2["cma_row"], raw_text[:50])
        return self._agreed_result(v3_v2, context, confidence=0.85, method="scoped_debate")

    # Still disagree → DOUBT
    logger.info("DOUBT: still disagree V3=%d vs Flash=%d for '%s'", v3_v2["cma_row"], flash_v2["cma_row"], raw_text[:50])
    return self._make_doubt(
        f"Models disagree after debate. V3: row {v3_v2['cma_row']} ({v3_v2.get('reasoning','')}), "
        f"Flash: row {flash_v2['cma_row']} ({flash_v2.get('reasoning','')})"
    )
```

#### 3. Model Call Method
```python
def _call_model(self, model_id: str, prompt: str) -> dict:
    """Call a single model via OpenRouter. Returns parsed dict with cma_row, reasoning, etc."""
    response = self._openrouter.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "You are a CMA classification expert. Respond with ONLY valid JSON."},
            {"role": "user", "content": prompt + "\n\nRespond with ONLY this JSON format:\n{\"cma_row\": <integer>, \"cma_code\": \"<code>\", \"confidence\": <0.0-1.0>, \"reasoning\": \"<brief>\"}"},
        ],
        max_tokens=200,
        temperature=0.0,
    )
    text = response.choices[0].message.content.strip()
    # Parse JSON from response (handle markdown code blocks)
    if "```" in text:
        text = text.split("```")[1].strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)
```

#### 4. Debate Prompt Builder
```python
def _build_debate_prompt(self, original_prompt: str, v3_result: dict, flash_result: dict) -> str:
    return f"""{original_prompt}

Two AI models disagreed on this classification:

Model A chose Row {v3_result['cma_row']} ({v3_result.get('cma_code', '?')}): {v3_result.get('reasoning', 'no reason given')}
Model B chose Row {flash_result['cma_row']} ({flash_result.get('cma_code', '?')}): {flash_result.get('reasoning', 'no reason given')}

Carefully consider both arguments and pick the BEST answer. Respond with ONLY this JSON format:
{{"cma_row": <integer>, "cma_code": "<code>", "confidence": <0.0-1.0>, "reasoning": "<brief>"}}"""
```

#### 5. Result Builders
```python
def _agreed_result(self, model_result: dict, context: _ScopedContext, confidence: float, method: str) -> AIClassificationResult:
    cma_row = int(model_result.get("cma_row", 0))
    label = self._labels_by_row.get(cma_row)
    cma_field_name = label["name"] if label else model_result.get("cma_code", "UNCLASSIFIED")
    broad = _SECTION_TO_BROAD.get(context.section_normalized, "admin_expense")
    return AIClassificationResult(
        cma_field_name=cma_field_name,
        cma_row=cma_row,
        cma_sheet="input_sheet",
        broad_classification=broad,
        confidence=confidence,
        is_doubt=False,
        doubt_reason=None,
        alternatives=[],
        classification_method=method,
    )

def _single_model_result(self, model_result: dict, context: _ScopedContext, method: str) -> AIClassificationResult:
    return self._agreed_result(model_result, context, confidence=0.75, method=method)
```

#### 6. Sync Wrapper (for pipeline.py compatibility)
Since pipeline.py calls `self._ai.classify(...)` synchronously but the debate is async, add a sync wrapper:

```python
def classify_sync(self, raw_text, amount, section, industry_type, document_type, fuzzy_candidates) -> AIClassificationResult:
    """Synchronous wrapper for classify(). Used by pipeline.py."""
    try:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self.classify(raw_text, amount, section, industry_type, document_type, fuzzy_candidates)
            )
        finally:
            loop.close()
    except Exception as e:
        logger.error("classify_sync failed: %s", e)
        return self._make_doubt(f"Classification error: {e}")
```

> **Note:** The original spec used `asyncio.get_event_loop()` which crashes in ARQ worker threads (no running event loop). The fix uses `asyncio.new_event_loop()` + `loop.close()` to create a fresh loop each time. This was bug #1 found during integration.

#### 7. Cost Guards (MANDATORY)
```python
# At module level:
MAX_TOKENS_PER_RUN = 500_000
MAX_ITEMS_PER_DOCUMENT = 300

# In __init__:
self._total_tokens = 0
self._items_classified = 0

# In _call_model, after the API call:
usage = response.usage
if usage:
    self._total_tokens += (usage.prompt_tokens or 0) + (usage.completion_tokens or 0)
    if self._total_tokens > MAX_TOKENS_PER_RUN:
        raise RuntimeError(f"Token budget exceeded: {self._total_tokens} > {MAX_TOKENS_PER_RUN}")

# Print cost summary every 10 items:
self._items_classified += 1
if self._items_classified % 10 == 0:
    logger.info("Cost guard: %d items, ~%d tokens used", self._items_classified, self._total_tokens)
```

### File 2: `backend/app/services/classification/pipeline.py` — TWO FIXES

**Fix 1: Use classify_sync (or handle async)**
Change line 165 to call the sync wrapper:
```python
# Line 165: Change from:
ai_result = self._ai.classify(...)
# To:
ai_result = self._ai.classify_sync(...)
```

**Fix 2: Use result's classification_method instead of hardcoded "ai_haiku"**
Change line 191 from:
```python
"classification_method": "ai_haiku",
```
To:
```python
"classification_method": ai_result.classification_method,
```

Also fix line 217 (doubt case):
```python
"classification_method": ai_result.classification_method,
```

### File 3: `backend/app/config.py` — ADD CLASSIFIER_MODE

Add to the Settings class:
```python
# Classification engine mode
classifier_mode: str = "scoped"  # "scoped" (new DeepSeek+Gemini debate) or "legacy" (old Haiku-only)
```

### File 4: `.env.example` — ADD CLASSIFIER_MODE

Add:
```
CLASSIFIER_MODE=scoped
```

### File 5: (Optional) Pipeline fallback — if CLASSIFIER_MODE=legacy

In `pipeline.py` __init__, add mode toggle:
```python
from app.config import get_settings

class ClassificationPipeline:
    def __init__(self) -> None:
        self._rules = RuleEngine()
        self._fuzzy = FuzzyMatcher()
        settings = get_settings()
        if settings.classifier_mode == "legacy":
            from app.services.classification.ai_classifier import AIClassifier
            self._ai = AIClassifier()
            self._use_sync = False
        else:
            self._ai = ScopedClassifier()
            self._use_sync = True  # scoped uses classify_sync
```

And in classify_item:
```python
if self._use_sync:
    ai_result = self._ai.classify_sync(...)
else:
    ai_result = self._ai.classify(...)
```

## Prompt Modification (in _build_prompt)

Update the INSTRUCTIONS section of the prompt to ask for JSON response instead of tool_use:
```python
"""...
INSTRUCTIONS:
1. Pick the BEST matching CMA row from the list above
2. If the item does NOT belong to any of these rows, set cma_row to 0
3. Set confidence to reflect how certain you are (0.8+ = confident, below = unsure)
4. Keep reasoning under 15 words

Respond with ONLY this JSON format:
{"cma_row": <integer>, "cma_code": "<code>", "confidence": <0.0-1.0>, "reasoning": "<brief>"}
"""
```

## Key Files Reference

| File | Mount in Docker | Purpose |
|------|----------------|---------|
| `CMA_Ground_Truth_v1/scripts/section_mapping.json` | `/app/CMA_Ground_Truth_v1/scripts/section_mapping.json` | 133 sections → 23 categories |
| `CMA_Ground_Truth_v1/scripts/sheet_name_mapping.json` | `/app/CMA_Ground_Truth_v1/scripts/sheet_name_mapping.json` | 46 sheet names → 6 forms |
| `CMA_Ground_Truth_v1/reference/canonical_labels.json` | `/app/CMA_Ground_Truth_v1/reference/canonical_labels.json` | 131 CMA row definitions (row offset fixed — rows now match Excel) |
| `CMA_Ground_Truth_v1/reference/cma_classification_rules.json` | `/app/CMA_Ground_Truth_v1/reference/cma_classification_rules.json` | 385 CA expert rules |
| `CMA_Ground_Truth_v1/database/training_data.json` | `/app/CMA_Ground_Truth_v1/database/training_data.json` | 1,326 training examples |

## Dependencies (already in requirements.txt)

- `openai>=1.60.0` — for OpenRouter API calls (OpenAI-compatible)
- `anthropic>=0.44.0` — keep for legacy mode; scoped mode does NOT use it

## What NOT To Do

- **DO NOT** modify the frontend
- **DO NOT** modify extraction pipeline
- **DO NOT** modify Excel generator
- **DO NOT** modify `rule_engine.py` or `fuzzy_matcher.py`
- **DO NOT** use `anthropic` package in the new scoped classifier — use `openai` package
- **DO NOT** create retry loops — if a model call fails, use the other model's answer; if both fail, flag as doubt
- **DO NOT** run accuracy tests — that's a separate session
- **DO NOT** use Anthropic API key — user has NO credits
- **DO NOT** restructure the project

## Verification Checklist

After making changes:
1. `docker compose build` succeeds (no import errors)
2. `docker compose up -d` starts all 4 services
3. Worker logs show: `ScopedClassifier ready: 23 sections, 131 canonical labels, 385 rules, ...`
4. Worker logs do NOT mention `anthropic` or `Anthropic` — only `openrouter`
5. A test classification (via browser or API) shows:
   - Worker logs: calls to `deepseek/deepseek-chat` and `google/gemini-2.0-flash-001`
   - Agreement/debate decisions logged
   - classification_method in DB is `scoped_agree` or `scoped_debate` (NOT `ai_haiku`)
6. `CLASSIFIER_MODE=legacy` in .env falls back to old Haiku classifier
7. Cost tracking appears in worker logs every 10 items

## Environment Variables Needed

```
OPENROUTER_API_KEY=sk-or-...  (already exists in .env)
CLASSIFIER_MODE=scoped        (new — add to .env)
```

The `ANTHROPIC_API_KEY` can be empty/invalid for the scoped mode — it's only used in legacy mode.

## Testing This Change

After Docker rebuilds, the fastest test is:
1. Open browser at `http://localhost:3002`
2. Login, go to an existing client with verified line items
3. Trigger classification
4. Watch `docker compose logs worker -f` for:
   - `AGREE round 1: row X for '...'`
   - `DISAGREE: V3=X vs Flash=Y for '...'`
   - `AGREE after debate: row X for '...'`
   - `DOUBT: still disagree...`
   - `Cost guard: N items, ~M tokens used`

If you see `anthropic.AuthenticationError` or `APIConnectionError` → you're still using the old Anthropic client. Check imports.
