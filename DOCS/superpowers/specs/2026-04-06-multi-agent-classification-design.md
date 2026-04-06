# Multi-Agent Classification System — Design Spec

**Date:** 2026-04-06
**Branch:** `feat/page-type-awareness`
**Status:** Approved — ready for implementation planning

---

## Problem

The current single-agent classifier (DeepSeek V3, one API call per item) achieves ~60% accuracy and 75% doubt rate on BCIPL (230 items). Root cause: DeepSeek V3's 64K context can't hold all 597 golden rules + domain knowledge simultaneously. It defaults to R71 "Others Admin" when unsure.

## Solution

Replace the single-agent classifier with a **5-agent pipeline**: 1 router + 4 specialists. Each specialist sees only its section's CMA rows and golden rules. Uses Gemini 2.5 Flash (1M context) via OpenRouter. Total: 5 API calls per document.

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Classification accuracy (vs GT) | ~60% | 85%+ |
| Doubt rate | 75% | <25% |
| API calls per document | 230 | 5 |
| Cost per document | ~$0.15 | ~$0.02 |

---

## Architecture

```
                        ALL VERIFIED LINE ITEMS
                                |
                    +---------------------------+
                    |   MultiAgentPipeline      |
                    |                           |
                    | 1. Fetch items from DB    |
                    | 2. Check learned_mappings |
                    |    (skip AI for matches)  |
                    +-------------+-------------+
                                  |
              +--- items NOT in learned_mappings ---+
              |                                     |
              v                                     v
    +------------------+                  Items matched by
    |   ROUTER AGENT   |                  learned_mappings
    |  Gemini 2.5 Flash|                  -> direct classify
    |  1 API call      |                     (no AI call)
    +--------+---------+
             |
    +--------+--------+--------+
    v        v        v        v
 pl_income pl_exp  bs_liab  bs_asset
    |        |        |        |
    +--------+--------+--------+
             | asyncio.gather (parallel)
             v
    +------------------+
    |    COMBINER      |  Pure code
    | merge + sign     |  amount x sign
    | + batch DB write |
    +------------------+
```

**Model:** `google/gemini-2.5-flash` via OpenRouter (stable, not preview).

**No fallback to old pipeline.** Old pipeline files are deleted. If router/specialist fails, affected items become doubts for CA review.

---

## Component 1: Router Agent

### Purpose
Receives ALL remaining items (after learned_mappings filter). Assigns each to one of 4 specialist buckets. **No skip bucket** — every item reaches a specialist.

### Input
```json
{
  "industry_type": "manufacturing",
  "document_type": "profit_and_loss",
  "items": [
    {
      "id": "uuid-001",
      "description": "Revenue from Operations",
      "amount": 1049700540,
      "section": "income",
      "source_sheet": "P & L Ac",
      "page_type": "face"
    }
  ]
}
```

### Output
```json
{
  "routing": [
    {"id": "uuid-001", "bucket": "pl_income", "reason": "Revenue line from P&L"},
    {"id": "uuid-002", "bucket": "bs_liability", "reason": "Term loan under borrowings"}
  ]
}
```

### Routing Signals (priority order)
1. **source_sheet** — strongest signal ("P & L" -> P&L agents, "Notes BS" -> B/S agents)
2. **section** header from extraction — narrows income vs expense, asset vs liability
3. **description** keywords — tiebreaker for ambiguous cases

### No Skipping
Every item gets routed to a specialist. The specialist decides if it can classify the item or if it becomes a doubt. Nothing is silently dropped.

---

## Component 2-5: Specialist Agents

All 4 specialists share the same prompt structure and output format.

### Agent Distribution

| Agent | CMA Rows | Golden Rules | Biggest Challenge |
|-------|----------|-------------|-------------------|
| P&L Income | 9 (R22-R34) | 52 | Domestic vs Export split |
| P&L Expense | 42 (R41-R108) | 350 | Manufacturing vs Admin split by industry |
| B/S Liability | 22 (R110-R160) | 84 | Individual bank loan accounts |
| B/S Asset | 58 (R161-R258) | 111 | Fixed asset schedules, current liabilities in asset range |

### Prompt Structure (5 Layers)

| Layer | Content | Source | Size |
|-------|---------|--------|------|
| L1: Identity | Role description + industry context | Hand-written template | ~100 words |
| L2: CMA Rows | Rows this agent can classify into (code + name) | Auto-gen from canonical_labels.json | 9-58 rows |
| L3: Golden Rules | CA-override first, then legacy. Filtered by row range + industry | Auto-gen from cma_golden_rules_v2.json | 52-350 rules |
| L4: Domain Knowledge | Indian accounting expertise, common traps, sign rules | Synthesized from golden rules + GT patterns | ~300-500 words |
| L5: Batch I/O | JSON schema for input/output arrays | Template | ~100 words |

### Layer 4 Synthesis (no CA interview needed)
The 597 golden rules already encode the CA's expertise. The prompt generation script analyzes them to extract:
- Industry-specific routing (manufacturing vs trading vs service)
- CA-override contradictions ("X goes to R{a}, NOT R{b}")
- Training examples from 9 GT companies

### Batch Input (from router)
```json
{
  "industry_type": "manufacturing",
  "items": [
    {
      "id": "uuid-001",
      "description": "Staff Welfare Expenses",
      "amount": 234500,
      "section": "employee benefit expenses"
    }
  ]
}
```

### Batch Output
```json
{
  "classifications": [
    {
      "id": "uuid-001",
      "cma_row": 67,
      "cma_code": "II_D1",
      "confidence": 0.95,
      "sign": 1,
      "reasoning": "Staff welfare -> Salary and staff expenses (CA override rule)"
    },
    {
      "id": "uuid-007",
      "cma_row": 22,
      "cma_code": "II_A1",
      "confidence": 0.90,
      "sign": -1,
      "reasoning": "Sales Returns subtracted from Domestic Sales"
    },
    {
      "id": "uuid-012",
      "cma_row": 0,
      "cma_code": "DOUBT",
      "confidence": 0.45,
      "sign": 1,
      "reasoning": "Ambiguous: could be R71 or R49, needs CA review",
      "alternatives": [
        {"cma_row": 71, "cma_code": "II_D5", "confidence": 0.45},
        {"cma_row": 49, "cma_code": "II_C9", "confidence": 0.40}
      ]
    }
  ]
}
```

### Key Design Decisions
- **sign field** — `1` (add) or `-1` (subtract). Orchestrator does `amount x sign` before DB write. Handles Sales Returns, Closing Stock, etc.
- **Doubt threshold** — confidence < 0.80 -> doubt (same as current)
- **alternatives on doubt** — top 2-3 candidates so CA sees options in review UI
- **FORMULA_ROWS guard** — rows 200, 201 excluded from L2. Specialists cannot classify into formula cells.
- **Face vs notes dedup** — specialists see `page_type` and `has_note_breakdowns` flag. When note breakdowns exist, face totals get classified as `cma_row: 0` (doubt) to prevent double-counting. CA can override.

---

## Orchestrator: MultiAgentPipeline

Replaces `ClassificationPipeline`. Single class, clean flow.

### Flow
```
classify_document(document_id, client_id, industry_type, ...)
    |
    +-- 1. Fetch all verified line items from DB
    |
    +-- 2. Check learned_mappings (one DB call)
    |     +-- Items with exact match -> classify immediately (no AI)
    |     +-- Remaining items -> send to router
    |
    +-- 3. Router call (1 Gemini call, all remaining items)
    |     -> returns {pl_income: [...], pl_expense: [...], bs_liability: [...], bs_asset: [...]}
    |
    +-- 4. Four specialist calls in parallel (asyncio.gather)
    |     -> skip empty buckets
    |     -> each returns list of classifications
    |
    +-- 5. Combine all results (learned + specialist-classified)
    |     +-- Apply sign: amount x sign
    |     +-- Set status: >= 0.85 "approved", 0.80-0.84 "auto_classified", < 0.80 "needs_review"
    |     +-- Single batch INSERT to classifications table
    |
    +-- 6. Return summary {total, high_confidence, medium_confidence, needs_review}
```

### Error Handling
- Router fails -> all items become doubts for CA review
- One specialist fails -> only that bucket's items become doubts, other buckets succeed
- Empty/null description items -> sent to router like any other item; specialist will doubt them
- No silent failures — every item gets a classification record

### Cost Guards
- `MAX_TOKENS_PER_RUN = 500,000`
- `MAX_ITEMS_PER_DOCUMENT = 500`
- Per-call token tracking via OpenRouter usage response

---

## Prompt Generation Script

`scripts/generate_agent_prompts.py` — auto-generates prompts from existing GT files.

### Input Files (all exist)
- `canonical_labels.json` — CMA rows with code, name, section
- `cma_golden_rules_v2.json` — 597 rules (CA overrides, interview, legacy)
- `training_data.json` — real examples from 9 companies

### Output
5 prompt files in `backend/app/services/classification/prompts/`:
- `router_prompt.md`
- `pl_income_prompt.md`
- `pl_expense_prompt.md`
- `bs_liability_prompt.md`
- `bs_asset_prompt.md`

### Layer 4 Synthesis Logic
The script analyzes golden rules to auto-generate domain knowledge:
- Rules where `industry_type = "manufacturing"` + row in manufacturing range -> "For manufacturing: these items go here"
- CA-override rules contradicting legacy -> "IMPORTANT: {item} goes to R{x}, NOT R{y}"
- Training examples grouped by specialist -> "Previous companies classified '{item}' -> R{x}"

### Deterministic
Same input files always produce the same prompts. When corrections get promoted to golden rules, re-running the script updates all prompts.

---

## Offline Eval Script

`scripts/eval_multi_agent.py` — tests accuracy against GT without Supabase or PDF extraction.

### What It Measures
| Metric | How |
|--------|-----|
| Accuracy | GT cma_row vs pipeline cma_row — exact match % |
| Doubt rate | % of items with confidence < 0.80 |
| Misroute rate | Items router sent to wrong specialist |
| Per-agent accuracy | Each specialist's accuracy on its own items |
| Confusion pairs | Most common mistakes (e.g., R45<->R67) |

### Usage
```bash
python scripts/eval_multi_agent.py --company BCIPL
python scripts/eval_multi_agent.py --all
python scripts/eval_multi_agent.py --company BCIPL --agent pl_expense
```

### Purpose
Fast iteration loop: change a prompt -> re-run eval -> see accuracy in 30 seconds. Then validate with live end-to-end test once accuracy looks good.

---

## File Changes

### Delete
- `backend/app/services/classification/pipeline.py`
- `backend/app/services/classification/scoped_classifier.py`
- `backend/app/services/classification/ai_classifier.py`
- `backend/app/services/classification/fuzzy_matcher.py`

### New Files
```
backend/app/services/classification/
+-- multi_agent_pipeline.py          # Orchestrator
+-- agents/
|   +-- base.py                      # Shared agent logic (API call, response parsing)
|   +-- router.py                    # Router agent
|   +-- pl_income.py                 # P&L Income specialist
|   +-- pl_expense.py                # P&L Expense specialist
|   +-- bs_liability.py              # B/S Liability specialist
|   +-- bs_asset.py                  # B/S Asset specialist
+-- prompts/
    +-- router_prompt.md
    +-- pl_income_prompt.md
    +-- pl_expense_prompt.md
    +-- bs_liability_prompt.md
    +-- bs_asset_prompt.md

scripts/
+-- generate_agent_prompts.py        # Prompt auto-generation
+-- eval_multi_agent.py              # Offline eval
```

### Modified
- `config.py` — remove `classifier_mode`, `classifier_model`. Add `gemini_model: str = "google/gemini-2.5-flash"`
- `classification_tasks.py` — `ClassificationPipeline()` -> `MultiAgentPipeline()`
- `__init__.py` — update module docstring

### Unchanged
- `excel_generator.py` — already handles formulas and per-item amounts
- `learning_system.py` — still reads/writes learned_mappings
- Frontend — still reads classifications table, shows doubts

---

## Future Enhancement (Not In Scope)

**Correction-to-rule promotion:** When the CA corrects a doubt, the correction currently saves to `learned_mappings`. Future system: high-confidence corrections (corrected N times across different companies) get promoted to golden rules automatically. Re-run prompt generation script to update specialist prompts.

This is deferred — current learned_mappings system handles the immediate feedback loop.
