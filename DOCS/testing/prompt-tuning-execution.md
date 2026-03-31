# Haiku Classification Prompt Tuning — Execution Prompt

Paste this into a **fresh Claude Code window** (Opus model). It will run a multi-phase prompt tuning experiment using Haiku subagents, entirely on your Claude Max subscription.

**Do NOT modify any app source code. This is a READ-ONLY experiment.**

---

## CONTEXT — Read These First (do NOT load into your context beyond what's needed)

You are tuning the AI classification prompt for the CMA Automation System. The app classifies Indian financial line items (e.g., "CRCA Sheets & Coils", "Interest on Term Loans") into 139 CMA fields (e.g., "Raw Materials Consumed (Indigenous)" → Row 42).

### Key Files (read these before starting):
```
backend/app/services/classification/ai_classifier.py    — Current prompt in _build_prompt() method (lines 422-478)
backend/app/mappings/cma_field_rows.py                  — All 139 CMA fields with row numbers
DOCS/extractions/BCIPL_classification_ground_truth.json — 267 items with correct answers (your eval dataset)
docs/superpowers/specs/2026-03-23-haiku-prompt-tuning-design.md — Full design spec
```

### Ground Truth Format (448 items across 6 sheets):
```json
{
  "raw_text": "CRCA Sheets and Coils",
  "amount_rupees": 784529387.42,
  "financial_year": 2021,
  "section": "note 20 - cost of raw materials consumed",
  "sheet_name": "Notes to P & L",
  "correct_cma_field": "Raw Materials Consumed (Indigenous)",
  "correct_cma_row": 42,
  "confidence_note": "verified",
  "reasoning": "..."
}
```

### Sheet Coverage (448 items):
| Sheet | Items | What it contains |
|-------|-------|------------------|
| Notes to P & L | 116 | Income/expense details (Notes 18-26) |
| Notes BS (1) | 6 | Share capital, reserves, deferred tax |
| Notes BS (2) | 124 | Loans, trade payables, other liabilities |
| Subnotes to PL | 20 | Sub-breakdowns of P&L expenses |
| Subnotes to BS | 62 | TDS, advances, receivables, creditors detail |
| Co., Deprn | 120 | Asset-wise depreciation (Gross Block, Accum Depr) |
```

### Current App Prompt (from ai_classifier.py:453-478):
The app sends ONE item at a time with: raw_text, amount, section, industry_type, document_type, fuzzy candidates, and the full list of 139 CMA fields. Read the actual `_build_prompt()` method for the exact format.

---

## CONSTRAINTS

1. **Max 45 Haiku agent spawns total** across all phases (448 items = ~30 batches of 15)
2. **Max 3 prompt revision iterations** (phases 4-6)
3. **Never modify source code** — this is evaluation only
4. **All output saved to:** `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/`
5. **Track token counts** — estimate input/output tokens per batch to build cost model
6. **Items with confidence_note="unknown"** are excluded from accuracy calculation
7. **Batch size: 15 items per Haiku agent**
8. **Run Haiku agents in FOREGROUND** (not background) — you need results before proceeding

---

## PHASE 1: PREPARE (no Haiku agents)

### 1a. Read the ground truth
```python
# Read and parse DOCS/extractions/BCIPL_classification_ground_truth.json
# Count total items, breakdown by FY, by sheet_name, by section
```

### 1b. Read the current prompt
Read `backend/app/services/classification/ai_classifier.py` — specifically the `_build_prompt()` method (lines 422-478). This is the BASELINE prompt you are evaluating.

### 1c. Read the CMA field list
Read `backend/app/mappings/cma_field_rows.py` — these are the 139 valid CMA fields.

### 1d. Deduplicate items
Group items by `raw_text` (case-insensitive). For duplicates across FYs, keep the one with the highest `confidence_note` (verified > high > inferred). Record the dedup mapping so results can be projected back to all 267 items.

Expected: ~350-400 unique items after dedup (448 total items across 3 FYs, 6 sheets including depreciation schedule).

### 1e. Create batches
Split the deduplicated items into batches of 15. Each batch should mix P&L and BS items for variety.

### 1f. Create output directory
```bash
mkdir -p "DOCS/test-results/bcipl/prompt-tuning-2026-03-23"
```

### 1g. Report preparation summary
Print:
```
PREPARATION COMPLETE
Total ground truth items: 267
Unique items after dedup: XX
Batches of 15: XX
Items excluded (unknown confidence): XX
```

---

## PHASE 2: BASELINE CLASSIFICATION (Haiku agents)

For each batch of 15 items, spawn a Haiku agent with `model: "haiku"`.

### Haiku Agent Prompt Template:

```
You are a financial analyst classifying line items for Indian CMA (Credit Monitoring Arrangement) documents.

I will give you {N} line items. For EACH item, classify it into exactly ONE CMA field.

COMPANY: BCIPL (Bagadia Chaitra Industries Private Limited)
INDUSTRY: Manufacturing (metal stamping, laminations, CRCA components)
DOCUMENT TYPE: Combined Financial Statement

VALID CMA FIELDS (use EXACT field name and row number):
{paste the full ALL_FIELD_TO_ROW from cma_field_rows.py, formatted as "Row XX: Field Name"}

CLASSIFICATION RULES:
1. Match each line item to the SINGLE most appropriate CMA field from the list above
2. Use the EXACT field name from the list — do not invent new names
3. Set confidence 0.0-1.0 based on certainty
4. If confidence < 0.8, set is_uncertain=true and explain why
5. NEVER guess silently — flag uncertainty
6. Consider industry type: Manufacturing firms have production-related expenses
7. The "section" and "sheet_name" tell you WHERE in the financial statement this item appeared — use this context
8. Items from "Notes to P & L" are income/expense items
9. Items from "Notes BS" are asset/liability items
10. Items from depreciation schedules are usually Row 56 (manufacturing) or Row 63 (admin)

LINE ITEMS TO CLASSIFY:

Item 1:
  Description: {raw_text}
  Amount: Rs {amount_rupees:,.2f}
  Section: {section}
  Sheet: {sheet_name}
  Financial Year: {financial_year}

Item 2:
  ...
(repeat for all items in batch)

Return a JSON array with your classification for each item. Use this exact format:
[
  {
    "item_index": 1,
    "raw_text": "exact raw_text from above",
    "classified_cma_field": "Exact CMA Field Name",
    "classified_cma_row": 42,
    "confidence": 0.95,
    "is_uncertain": false,
    "reasoning": "Brief 1-sentence reason"
  },
  ...
]

IMPORTANT: Return ONLY the JSON array. No other text.
```

### Execution:
1. Spawn Haiku agents in FOREGROUND (you need results immediately)
2. You may run 2-3 Haiku agents in PARALLEL if they are independent batches
3. Parse each agent's JSON response
4. If an agent returns malformed JSON, log the error and retry ONCE with same batch
5. Record approximate token count per batch (estimate from prompt length + response length)

### After all batches complete:
Save raw results to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/baseline_results.json`:
```json
{
  "timestamp": "ISO-8601",
  "prompt_version": "baseline (from ai_classifier.py)",
  "total_items": XX,
  "results": [
    {
      "raw_text": "...",
      "financial_year": 2021,
      "section": "...",
      "sheet_name": "...",
      "expected_cma_field": "...",
      "expected_cma_row": 42,
      "predicted_cma_field": "...",
      "predicted_cma_row": 44,
      "confidence": 0.85,
      "is_correct": false,
      "reasoning": "..."
    },
    ...
  ],
  "token_estimate": {
    "avg_input_tokens_per_item": XX,
    "avg_output_tokens_per_item": XX,
    "total_input_tokens": XX,
    "total_output_tokens": XX
  }
}
```

---

## PHASE 3: FAILURE ANALYSIS (no Haiku agents)

### 3a. Score results
For each item: `is_correct = (predicted_cma_row == expected_cma_row)`

### 3b. Calculate metrics
```
BASELINE RESULTS
================
Total items tested: XX
Correct: XX (XX.X%)
Wrong: XX (XX.X%)
Uncertain (confidence < 0.8): XX

By confidence level:
  >= 0.9: XX items, XX% correct
  0.8-0.89: XX items, XX% correct
  < 0.8: XX items, XX% correct

By sheet:
  Notes to P & L: XX/XX correct (XX%)
  Notes BS (1): XX/XX correct (XX%)
  Notes BS (2): XX/XX correct (XX%)
  Subnotes to PL: XX/XX correct (XX%)
  Subnotes to BS: XX/XX correct (XX%)
```

### 3c. Group failures by pattern
Analyze ALL wrong answers and group them:

| Pattern | Example | Count |
|---------|---------|-------|
| Section confusion | P&L item classified as BS field | X |
| Adjacent field | R41 (imported) vs R42 (indigenous) | X |
| Depreciation routing | Mfg depreciation vs Admin depreciation | X |
| Interest routing | Term loan vs WC vs bank charges | X |
| Others overflow | Specific field exists but "Others" chosen | X |
| Freight confusion | Manufacturing vs selling freight | X |
| Statutory dues | Wrong liability row | X |
| Other | ... | X |

### 3d. Save analysis
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/baseline_accuracy.md`

---

## PHASE 4: PATTERN INTERVIEW (Haiku agents)

For each failure pattern with 3+ items, spawn ONE Haiku agent with `model: "haiku"`:

### Interview Agent Prompt Template:

```
You are a financial analyst who classifies Indian CMA line items.
You classified some items INCORRECTLY. I need to understand WHY so I can improve the classification prompt.

FAILURE PATTERN: {pattern_name}
(e.g., "Depreciation Routing — manufacturing vs admin")

ITEMS YOU GOT WRONG:

1. "{raw_text}" (Sheet: {sheet_name}, Section: {section})
   Your answer: {predicted_cma_field} (Row {predicted_cma_row})
   Correct answer: {expected_cma_field} (Row {expected_cma_row})

2. ...
(up to 10 examples per pattern)

QUESTIONS — answer each one:

1. PROMPT WEAKNESS: What in the classification prompt made you choose the wrong field? Was there ambiguity? Missing context?

2. MISSING KNOWLEDGE: What additional information would have helped you get ALL of these right? Be specific — what exact sentence or rule should be in the prompt?

3. DETERMINISTIC RULE: Is there a simple pattern-matching rule that could classify ALL items in this group correctly WITHOUT needing AI?
   Format: IF description contains [X] AND section contains [Y] THEN cma_row = [Z]
   (These become Rule Engine rules that skip AI entirely, saving cost)

4. SECTION SIGNAL: Did the "section" and "sheet_name" fields help or confuse you? How should they be used?

5. FIELD GROUPING: Would it help if the 139 CMA fields were grouped by category (P&L Income, P&L Manufacturing Expenses, P&L Admin Expenses, BS Assets, BS Liabilities) instead of a flat numbered list?

Return your answers as structured JSON:
{
  "pattern": "{pattern_name}",
  "prompt_weakness": "...",
  "missing_knowledge": "...",
  "deterministic_rules": [
    {
      "condition": "IF description contains 'X' AND section contains 'Y'",
      "cma_field": "...",
      "cma_row": XX,
      "covers_items": [1, 2, 3]
    }
  ],
  "section_signal_feedback": "...",
  "field_grouping_feedback": "...",
  "suggested_prompt_additions": ["sentence 1 to add", "sentence 2 to add"]
}
```

### After all interviews:
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/interview_responses.json`

---

## PHASE 5: PROMPT REVISION (no Haiku agents)

Based on interview responses, create a REVISED prompt. Save it to:
`DOCS/test-results/bcipl/prompt-tuning-2026-03-23/revised_prompt_v1.txt`

### Potential improvements to consider:
1. **Group CMA fields by category** instead of flat list:
   ```
   === P&L — INCOME (Rows 22-34) ===
   Row 22: Domestic Sales
   Row 23: Export Sales
   ...
   === P&L — MANUFACTURING EXPENSES (Rows 41-56) ===
   Row 41: Raw Materials Consumed (Imported)
   ...
   ```

2. **Section-aware routing hints:**
   - "Items from 'Notes to P & L' are ALWAYS income or expense items — never assets or liabilities"
   - "Items from 'Notes BS' are ALWAYS assets or liabilities — never income or expenses"

3. **Common confusion pairs** (from interview findings):
   - "Row 41 = Imported materials, Row 42 = Indigenous materials — check for 'import' or 'customs' in description"
   - "Row 56 = Manufacturing depreciation (production assets), Row 63 = Admin depreciation (office/vehicle)"

4. **Industry-specific hints:**
   - "Manufacturing: freight/transport charges → Row 47 (manufacturing), NOT Row 70 (selling)"
   - "Manufacturing: factory rent → Row 49 (manufacturing), NOT Row 68 (admin rent)"

5. **Deterministic rules from interviews** (these become Rule Engine candidates too)

---

## PHASE 6: RE-TEST (Haiku agents)

### 6a. Re-test failed items only
Take ALL items that were WRONG in Phase 2. Send them through Haiku agents using the REVISED prompt (same batch format, 15 items per agent).

### 6b. Compare
```
RE-TEST RESULTS (Prompt V1)
===========================
Previously failed items: XX
Now correct: XX (XX.X% recovery)
Still wrong: XX
New failures (were correct, now wrong): 0 (check this!)

Overall accuracy:
  Baseline: XX/YY (ZZ.Z%)
  After V1:  XX/YY (ZZ.Z%)
  Improvement: +X.X percentage points
```

### 6c. Iterate if needed
If recovery rate < 50% of failed items, do ONE more iteration:
- Interview remaining failures (Phase 4 again)
- Revise prompt to V2 (Phase 5 again)
- Re-test (Phase 6 again)

Max 3 total iterations. After 3, stop and report.

---

## PHASE 7: DELIVERABLES (no Haiku agents)

### Deliverable 1: Final Optimized Prompt
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/final_prompt.txt`

This is the complete `_build_prompt()` method body, ready to copy into `ai_classifier.py`. Include the full Python method with all improvements.

### Deliverable 2: Cost Model
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/cost_model.md`

```markdown
# CMA Classification Cost Model

## Token Analysis (BCIPL, per item)
| Metric | Baseline Prompt | Optimized Prompt |
|--------|----------------|-----------------|
| Input tokens | ~X,XXX | ~X,XXX |
| Output tokens | ~XXX | ~XXX |
| Total per item | ~X,XXX | ~X,XXX |

## Cost Projection (OpenRouter, Claude Haiku)
| Rate | Input: $0.80/M tokens | Output: $4.00/M tokens |
|------|----------------------|----------------------|

| Scenario | Items | Input Cost | Output Cost | Total |
|----------|-------|-----------|-------------|-------|
| BCIPL (3 docs, all items) | ~267 | $X.XX | $X.XX | $X.XX |
| BCIPL (after Rule Engine) | ~XX | $X.XX | $X.XX | $X.XX |
| Avg company (est.) | ~200 | $X.XX | $X.XX | $X.XX |
| 7 companies total | ~1400 | $X.XX | $X.XX | $X.XX |

## Cost Savings from Rule Engine
| Stage | Items | Cost |
|-------|-------|------|
| Total items | 267 | - |
| Handled by Rule Engine (Tier 0, free) | ~XX | $0.00 |
| Handled by Fuzzy Match (Tier 1, free) | ~XX | $0.00 |
| Reaching AI (Tier 2, paid) | ~XX | $X.XX |
| **Net cost per company** | | **$X.XX** |
```

### Deliverable 3: Rule Candidates
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/rule_candidates.json`

```json
[
  {
    "rule_id": "BCIPL-NEW-XXX",
    "pattern_description": "human-readable description",
    "regex_pattern": "regex for rule_engine.py",
    "condition": "IF description matches X AND section/sheet Y",
    "correct_cma_field": "Exact CMA Field Name",
    "correct_cma_row": 42,
    "confidence": 0.95,
    "source": "Haiku interview — {pattern name}",
    "items_covered": ["item1 raw_text", "item2 raw_text"],
    "needs_ca_verification": true
  }
]
```

### Deliverable 4: Final Report
Save to `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/FINAL_REPORT.md`

```markdown
# Haiku Prompt Tuning — BCIPL Results

## Summary
| Metric | Baseline | Final | Change |
|--------|----------|-------|--------|
| Accuracy | XX.X% | XX.X% | +XX.X pp |
| Doubt rate | XX.X% | XX.X% | -XX.X pp |
| Avg confidence | 0.XX | 0.XX | +0.XX |

## Prompt Iterations
| Version | Accuracy | Key Changes |
|---------|----------|-------------|
| Baseline | XX.X% | Original ai_classifier.py prompt |
| V1 | XX.X% | [what changed] |
| V2 | XX.X% | [what changed] |

## Top Failure Patterns (remaining)
| Pattern | Count | Why Still Failing |
|---------|-------|------------------|
| ... | ... | ... |

## New Rule Candidates
| Rule | Pattern | CMA Row | Items Covered |
|------|---------|---------|---------------|
| ... | ... | ... | ... |

## Cost Model Summary
- Cost per item (optimized): $X.XXXX
- Cost per BCIPL (267 items, no rules): $X.XX
- Cost per BCIPL (after rules, ~XX items to AI): $X.XX
- Projected savings from rules: XX%

## Recommendations
1. ...
2. ...
3. ...
```

---

## QUICK REFERENCE

| Resource | Path |
|----------|------|
| Ground truth | `DOCS/extractions/BCIPL_classification_ground_truth.json` |
| Current prompt | `backend/app/services/classification/ai_classifier.py:422-478` |
| CMA fields | `backend/app/mappings/cma_field_rows.py` |
| Rule Engine | `backend/app/services/classification/rule_engine.py` |
| Design spec | `docs/superpowers/specs/2026-03-23-haiku-prompt-tuning-design.md` |
| Output dir | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/` |

## AGENT SPAWN BUDGET

| Phase | Haiku Agents | Purpose |
|-------|-------------|---------|
| Phase 2 (classify) | ~30 | 15 items each, 448 items baseline |
| Phase 4 (interview) | ~5 | 1 per failure pattern |
| Phase 6 (re-test) | ~5 | failed items only |
| Phase 4b (interview V2) | ~3 | if needed |
| Phase 6b (re-test V2) | ~3 | if needed |
| **Total budget** | **~46** | **Max 50** |

---

**START by reading the 4 key files listed at the top. Then execute Phase 1 through Phase 7 in order. Do not skip phases.**
