# Session Log — 2026-03-23 (Part 2)
## CMA Project: Haiku Prompt Tuning Experiment

### What We Did

Ran a structured experiment to optimize the AI classification prompt by using Claude Haiku subagents inside Claude Code, comparing results against ground truth, interviewing failures, and generating rule candidates.

---

### Phase 0: Planning & Ground Truth Creation

#### 0a. Brainstormed the approach
- Read cold-start prompt (`DOCS/testing/cold-start-prompt.md`)
- Read project orientation files (BCIPL E2E test, session fixes, Rule Engine V2)
- Searched web for LLM prompt tuning best practices, Claude Code subagent patterns
- Decided on 5-phase approach: Prepare → Classify → Analyze → Interview → Re-test

#### 0b. Created ground truth for BCIPL
- **Agent 1 (Sonnet):** Reverse-engineered `BCIPL_classification_ground_truth.json` from CMA Excel INPUT SHEET + extracted data. 267 items.
- **Agent 2 (Sonnet):** Enriched with real `sheet_name` and `section` fields from actual Excel sheets. 267/267 enriched.
- **Agent 3 (Sonnet):** Added missing sheets — Co. Depreciation (120 items), Subnotes to BS expansion (61 items), Capital WIP (3 items from Notes BS), Def Tax (12 items, later removed per user instruction).
- **Final ground truth:** 448 items, 6 sheets, 3 FYs, 0 missing fields.

#### Files created:
```
DOCS/extractions/BCIPL_classification_ground_truth.json     — 448 items (the eval dataset)
docs/superpowers/specs/2026-03-23-haiku-prompt-tuning-design.md — Full design spec
DOCS/testing/prompt-tuning-execution.md                     — Execution prompt (7 phases)
```

#### Ground Truth Structure:
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

#### Sheet Distribution (448 items):
| Sheet | Items |
|-------|-------|
| Notes to P & L | 116 |
| Notes BS (1) | 6 |
| Notes BS (2) | 124 |
| Subnotes to PL | 20 |
| Subnotes to BS | 62 |
| Co., Deprn | 120 |

---

### Phase 1: Prompt Tuning Experiment (run in separate window)

The execution prompt (`DOCS/testing/prompt-tuning-execution.md`) was run in a fresh Claude Code window. It executed 7 phases using Haiku agents.

**Note:** This run accidentally used OpenRouter API calls instead of Claude Code Haiku subagents, costing ~$0.50. The execution prompt was later updated to explicitly require `Agent(model="haiku")` for future runs.

#### Results:

| Metric | Baseline | Optimized V1 | Change |
|--------|----------|-------------|--------|
| Accuracy | 78.4% (276/352) | 92.0% (324/352) | +13.6pp |
| Failures | 76 | 28 | -63% |
| Recovery | — | 80.5% (62/77 fixed) | — |
| Regressions | — | 13 (all corrected in final prompt) | — |
| Expected final | — | ~95-96% | — |

#### Top Failure Patterns (Baseline):
1. **Adjacent field confusion** (48.7%) — right category, wrong specific row
2. **Depreciation routing** (10.5%) — P&L vs manufacturing vs admin
3. **Loan classification** (9.2%) — Director loans as quasi-equity vs dues
4. **Employee expenses** (6.6%) — Directors Remuneration → R67 not R73
5. **Statutory dues** (5.3%) — TDS = advance tax, not liability
6. **Others overflow** (3.9%) — specific field exists but "Others" chosen

#### Key Findings:
- Grouping CMA fields by category (14 groups) eliminated most adjacent-field confusion
- 3-step routing (Sheet → Section → Description) prevented cross-category errors
- AI self-diagnosis (interviews) finds problems well but solves them unreliably — 13 regressions came from wrong interview answers
- Subnotes to PL was worst sheet at 36.8% baseline accuracy

#### Files produced:
```
DOCS/test-results/bcipl/prompt-tuning-2026-03-23/
├── baseline_results.json          — Raw baseline classification data
├── baseline_accuracy.md           — Detailed accuracy report with all failures
├── interview_responses.json       — Haiku interview answers per failure pattern
├── revised_prompt_v1.txt          — V1 prompt (before regression fixes)
├── retest_v1_results.json         — V1 retest results
├── final_prompt.txt               — BCIPL-specific optimized prompt (287 lines)
├── cost_model.md                  — Token counts + cost projections
├── rule_candidates.json           — 20 deterministic rules for Rule Engine
├── deduped_items.json             — Deduplication data
└── FINAL_REPORT.md                — Complete experiment report
```

---

### Phase 2: Generic Prompt Template

After the experiment, we realized the final prompt was BCIPL-specific (hardcoded company name and manufacturing rules). We created a generic version:

#### Changes from BCIPL-specific to generic:
- Removed hardcoded "BCIPL" company name → `{industry_type}` parameter
- Split disambiguation rules into:
  - **Universal** (all Indian companies) — Director Loans, TDS, Depreciation, S&D, etc.
  - **Manufacturing-specific** — Machinery Maintenance, Factory Rent, Production Depreciation
  - **Trading-specific** — Purchase of goods for resale, Import duty, Vendor discounts
  - **Partnership-specific** — Partners' Capital, Partners' Salary, Interest to Partners
- Kept grouped CMA fields (structural improvement, universal)
- Kept 3-step routing hierarchy (universal)

#### File created:
```
DOCS/test-results/bcipl/prompt-tuning-2026-03-23/generic_prompt_template.txt
```

---

### Phase 3: Validation Run (in progress in separate window)

Running the generic prompt against BCIPL ground truth using Haiku subagents (this time via Agent tool, not OpenRouter).

#### Execution prompt:
```
DOCS/testing/prompt-validation-execution.md
```

#### Expected result: 95-96% accuracy (validates genericization didn't lose BCIPL-specific knowledge)

---

### Phase 4: SR Papers Ground Truth Extraction (in progress in separate window)

Creating ground truth for the next company (SR Papers, Trading industry) using the same methodology as BCIPL.

#### Execution prompt:
```
DOCS/testing/sr-papers-ground-truth-extraction.md
```

#### SR Papers Details:
| Field | Value |
|-------|-------|
| Company | S.R. Papers Private Limited |
| Industry | Trading (paper distribution, import-heavy) |
| Source Files | 3 × .xls (FY2024, FY2025, FY2026) |
| Ground Truth CMA | CMA S.R.Papers 09032026 v2.xls |
| Source Unit | Rupees |
| CMA Output Unit | Crores (B13 = "In Crs") |

---

### Cost Summary

| Activity | Cost | Source |
|----------|------|--------|
| Ground truth creation (3 Sonnet agents) | $0 | Claude Max |
| Prompt tuning experiment (55 Haiku calls) | ~$0.50 | OpenRouter (accidental) |
| Validation run (Haiku subagents) | $0 | Claude Max |
| SR Papers extraction (Sonnet agent) | $0 | Claude Max |
| **Total** | **~$0.50** | |

---

### Deliverables Summary

| Deliverable | File | Status |
|-------------|------|--------|
| BCIPL ground truth (448 items) | `DOCS/extractions/BCIPL_classification_ground_truth.json` | Done |
| Design spec | `docs/superpowers/specs/2026-03-23-haiku-prompt-tuning-design.md` | Done |
| Baseline accuracy report | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/baseline_accuracy.md` | Done |
| Final BCIPL-specific prompt | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/final_prompt.txt` | Done |
| Generic prompt template | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/generic_prompt_template.txt` | Done |
| 20 rule candidates | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/rule_candidates.json` | Done |
| Cost model | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/cost_model.md` | Done |
| Full experiment report | `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/FINAL_REPORT.md` | Done |
| Execution prompt (tuning) | `DOCS/testing/prompt-tuning-execution.md` | Done |
| Execution prompt (validation) | `DOCS/testing/prompt-validation-execution.md` | Done |
| SR Papers extraction prompt | `DOCS/testing/sr-papers-ground-truth-extraction.md` | Done |
| SR Papers ground truth | `DOCS/extractions/SR_Papers_classification_ground_truth.json` | In progress |

---

### How to Reproduce This for Any Company

#### Step 1: Create ground truth
Use the extraction prompt template pattern (like `sr-papers-ground-truth-extraction.md`):
1. Discover all sheets in source Excel files
2. Extract line items from Notes, Depreciation, Subnotes (skip TB, Cash Flow, Def Tax)
3. Cross-reference against CMA ground truth file
4. Save as `DOCS/extractions/{COMPANY}_classification_ground_truth.json`

#### Step 2: Run prompt tuning (optional — only needed once to establish the generic prompt)
Use `DOCS/testing/prompt-tuning-execution.md` as template. Already done for BCIPL.

#### Step 3: Run validation
Use `DOCS/testing/prompt-validation-execution.md` as template:
1. Fill in `{industry_type}` and select correct industry-specific rules section
2. Run against ground truth using Haiku subagents
3. Check accuracy meets threshold (>= 93% good, >= 95% excellent)

#### Step 4: Generate new rules
From validation failures, identify deterministic patterns → add to `rule_engine.py` after CA verification.

---

### Key Lessons Learned This Session

1. **AI interviews find problems but don't reliably solve them** — 13 regressions came from wrong Haiku self-diagnosis. Always validate against ground truth.

2. **Grouped CMA fields > flat list** — The single biggest accuracy improvement came from organizing 139 fields into 14 categories. Structure matters more than instructions.

3. **Section/sheet context is critical** — "Interest Received" from P&L notes = Row 30 (income). From BS notes = Row 247 (liability). The original prompt under-used this signal.

4. **Generic prompt works because most rules are universal Indian CMA conventions** — Director Loans = quasi-equity, TDS = advance tax, Depreciation P&L = Row 63. These aren't BCIPL-specific.

5. **Haiku subagents must use Agent(model="haiku"), NOT external API calls** — The first run accidentally used OpenRouter ($0.50). Fixed in prompt with explicit warnings.

6. **Ground truth creation is the hardest part** — Takes 3 Sonnet agents and careful cross-referencing. But it's reusable forever for that company.

7. **Cost is negligible** — Even via OpenRouter, classifying all 7 companies costs ~$0.71. The real value is in accuracy improvement and rule discovery.

---

*Session log generated: 2026-03-23 | Prompt Tuning Experiment + SR Papers Extraction*
