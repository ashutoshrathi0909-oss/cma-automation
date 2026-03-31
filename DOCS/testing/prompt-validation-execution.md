# Prompt Validation Run — Generic Prompt on BCIPL

Paste this into a **fresh Claude Code window** (Opus model). It validates the generic optimized prompt against the BCIPL ground truth using Haiku subagents — zero external API cost.

**Expected result: ~95-96% accuracy. If it drops below 90%, the genericization lost too much.**

---

## CRITICAL RULE — READ THIS FIRST

```
DO NOT call any external API (OpenRouter, Anthropic API, etc.).
DO NOT write Python scripts that make HTTP calls to AI models.
DO NOT import anthropic, openai, or requests to call AI endpoints.

INSTEAD: Use the Agent tool with model: "haiku" to spawn Haiku subagents.
This uses your Claude Max subscription — ZERO external cost.

Example:
  Agent(
    description="Classify batch 1",
    model="haiku",
    prompt="[your prompt here with the items]"
  )

EVERY classification must go through Agent(model="haiku"), nothing else.
```

---

## FILES TO READ

```
DOCS/test-results/bcipl/prompt-tuning-2026-03-23/generic_prompt_template.txt  — The prompt to validate
DOCS/extractions/BCIPL_classification_ground_truth.json                       — 448 items, ground truth
backend/app/mappings/cma_field_rows.py                                        — CMA field definitions (for reference)
```

---

## PHASE 1: PREPARE

### 1a. Read the generic prompt template
Read `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/generic_prompt_template.txt`

This prompt has `{industry_type}`, `{document_type}`, and `{industry_rules}` placeholders. For BCIPL:
- `{industry_type}` = "Manufacturing (metal stamping, laminations, CRCA components)"
- `{document_type}` = "Combined Financial Statement"
- `{industry_rules}` = Include the MANUFACTURING-SPECIFIC RULES section. Remove TRADING-SPECIFIC and PARTNERSHIP-SPECIFIC sections.

### 1b. Read and deduplicate ground truth
Read `DOCS/extractions/BCIPL_classification_ground_truth.json` (448 items).

Deduplicate by `raw_text` (case-insensitive). For duplicates across FYs, keep the one with the highest confidence_note (verified > high > inferred). Record the dedup mapping.

Expected: ~350 unique items.

### 1c. Create batches
Split deduplicated items into batches of 15. Mix P&L and BS items.

### 1d. Create output directory
```bash
mkdir -p "DOCS/test-results/bcipl/prompt-validation-2026-03-23"
```

### 1e. Print summary
```
PREPARATION COMPLETE
Total items: 448
Unique after dedup: XX
Batches: XX
Prompt: generic_prompt_template.txt (with Manufacturing rules)
```

---

## PHASE 2: CLASSIFY ALL ITEMS (Haiku subagents)

For each batch, spawn a Haiku agent using the Agent tool:

```
Agent(
  description="Classify batch N of M",
  model="haiku",
  prompt="[generic prompt template with placeholders filled in]\n\nLINE ITEMS TO CLASSIFY:\n\nItem 1:\n  Description: {raw_text}\n  Amount: Rs {amount_rupees:,.2f}\n  Section: {section}\n  Sheet: {sheet_name}\n  Financial Year: {financial_year}\n\nItem 2:\n  ...\n(15 items per batch)"
)
```

### Rules:
1. Use `model: "haiku"` on EVERY Agent call — this is mandatory
2. Run agents in FOREGROUND (you need results before proceeding)
3. You may run 2-3 agents in PARALLEL for independent batches
4. If an agent returns malformed JSON, retry ONCE
5. Parse the JSON response and extract classified_cma_row for each item
6. Track approximate token counts (estimate from prompt length)

---

## PHASE 3: SCORE AND REPORT

### 3a. Compare results
For each item: `is_correct = (predicted_cma_row == expected_cma_row)`

### 3b. Calculate metrics

```
VALIDATION RESULTS — Generic Prompt on BCIPL
=============================================
Total items: XX
Correct: XX (XX.X%)
Wrong: XX (XX.X%)

Previous experiment results for comparison:
  Baseline (flat prompt):    78.4% (276/352)
  BCIPL-specific V1:         92.0% (324/352)
  Expected (final w/ fixes): ~95-96%
  THIS RUN (generic):        XX.X%

Accuracy by sheet:
  Notes to P & L:  XX/XX (XX.X%)
  Notes BS (1):    XX/XX (XX.X%)
  Notes BS (2):    XX/XX (XX.X%)
  Subnotes to PL:  XX/XX (XX.X%)
  Subnotes to BS:  XX/XX (XX.X%)
  Co., Deprn:      XX/XX (XX.X%)

Accuracy by confidence:
  >= 0.9:    XX items, XX% correct
  0.8-0.89:  XX items, XX% correct
  < 0.8:     XX items, XX% correct
```

### 3c. Regression check
Compare against BCIPL-specific results. For each item:
- **Same as BCIPL-specific V1?** → No concern
- **Was wrong in V1, now correct?** → Generic prompt caught something V1 missed
- **Was correct in V1, now wrong?** → Genericization regression — document which rule was lost

### 3d. Failure analysis
List ALL wrong items grouped by pattern:

| Pattern | Count | Examples |
|---------|-------|---------|
| Adjacent field | X | ... |
| Depreciation | X | ... |
| ... | ... | ... |

### 3e. Token usage and cost projection
```
Token Analysis:
  Avg input tokens per batch: ~XX
  Avg output tokens per batch: ~XX
  Total input tokens: ~XX
  Total output tokens: ~XX

Cost projection (if this were OpenRouter):
  Input ($0.80/M): $X.XX
  Output ($4.00/M): $X.XX
  Total per BCIPL: $X.XX
  Projected per company: $X.XX
  Projected 7 companies: $X.XX
```

---

## PHASE 4: SAVE RESULTS

Save ALL results to `DOCS/test-results/bcipl/prompt-validation-2026-03-23/`:

### validation_results.json
```json
{
  "timestamp": "ISO-8601",
  "prompt_version": "generic_prompt_template (manufacturing rules)",
  "total_items": XX,
  "accuracy": XX.X,
  "correct": XX,
  "wrong": XX,
  "results": [
    {
      "raw_text": "...",
      "financial_year": 2021,
      "section": "...",
      "sheet_name": "...",
      "expected_cma_field": "...",
      "expected_cma_row": 42,
      "predicted_cma_field": "...",
      "predicted_cma_row": 42,
      "confidence": 0.95,
      "is_correct": true,
      "reasoning": "..."
    }
  ],
  "token_estimate": {
    "avg_input_per_batch": XX,
    "avg_output_per_batch": XX,
    "total_input": XX,
    "total_output": XX
  }
}
```

### VALIDATION_REPORT.md
Complete report with:
1. Summary table (accuracy, comparison vs baseline and V1)
2. Accuracy by sheet
3. Accuracy by confidence level
4. All wrong items with details
5. Regressions from V1 (if any)
6. Token usage and cost projection
7. Verdict: PASS (>= 93%) / MARGINAL (90-93%) / FAIL (< 90%)
8. Recommendations (if accuracy dropped, which rules to add back)

---

## CONSTRAINTS

1. **ALL classification via Agent(model="haiku")** — NO external API calls
2. **Max 30 Haiku agent spawns** (should be ~24 for classification + buffer for retries)
3. **Do NOT modify any source code**
4. **Run agents in FOREGROUND** (need results before scoring)
5. **Items with confidence_note="unknown" excluded** from accuracy calculation
6. **Batch size: 15 items per agent**

---

## VERDICT CRITERIA

| Accuracy | Verdict | Action |
|----------|---------|--------|
| >= 95% | EXCELLENT | Generic prompt is production-ready |
| 93-95% | GOOD | Minor industry-specific rules may help, but acceptable |
| 90-93% | MARGINAL | Some BCIPL-specific rules were load-bearing, need to add back as manufacturing rules |
| < 90% | FAIL | Genericization lost too much, investigate which rules broke |

---

**START by reading the 3 files listed above. Then execute Phase 1 through Phase 4 in order.**
