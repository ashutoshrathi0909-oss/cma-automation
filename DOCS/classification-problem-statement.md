# CMA Classification Problem — Comprehensive Technical Brief

**Date:** 2026-03-24
**Project:** CMA Automation System
**Author:** Ashutosh (product owner) + Claude (engineering partner)
**Purpose:** Full context for anyone helping solve the classification accuracy problem

---

## 1. What Is This Project?

We are building a web application that automates **CMA (Credit Monitoring Arrangement)** document preparation for an Indian Chartered Accountant (CA) firm. CMA is a standardized financial report format required by Indian banks when companies apply for loans.

**The workflow:**
1. CA uploads a client's financial statements (Excel/PDF — P&L, Balance Sheet, Notes, Schedules)
2. System extracts every line item (e.g., "ESI Payable ₹3,42,000")
3. **System classifies each line item into one of 139 fixed CMA fields** ← THIS IS THE PROBLEM
4. System generates the final CMA Excel report (.xlsm with macros)

Step 3 is the bottleneck. A human CA currently does this manually — reading each line item and deciding which CMA row it belongs to. We want to automate it with >93% accuracy so the CA only reviews ~50-100 items instead of 500-700.

---

## 2. The Classification Task (Formal Definition)

**Input:** A tuple of (raw_text, sheet_name, section, industry_type)
- `raw_text`: The line item description from the financial statement (e.g., "ESI Payable", "Axis Bank Sellers Credit - Ming Xu III", "Net GST Local Sales")
- `sheet_name`: Which sheet it came from (e.g., "Notes to P & L", "Notes BS (2)", "Co., Deprn")
- `section`: The section heading in the source document (e.g., "employee benefit expenses", "revenue from operations", "other current liabilities")
- `industry_type`: The type of business (e.g., "manufacturing", "trading", "partnership")

**Output:** One of 139 fixed CMA field rows (e.g., Row 22 = "Domestic Sales", Row 45 = "Wages", Row 246 = "Other statutory liabilities")

**Why it's hard:**

### 2a. Extreme vocabulary variance
The same financial concept appears as wildly different text across companies:
- "ESI Payable" / "Statutory Remittances Pending" / "Employee State Insurance Due" → all mean Row 246
- "PF Contribution" / "Provident Fund Deposit" / "EPF A/c" → all mean Row 45 or 246 depending on context
- There is no controlled vocabulary in Indian financial statements. Every CA firm, every auditor uses different wording.

### 2b. Context-dependent classification (same text → different CMA rows)
- "Interest Received" in P&L notes → Row 30 (Income)
- "Interest Received" in Balance Sheet notes → Row 247 (Accrued liability)
- "Job Work Charges" in revenue section → Row 22 (Domestic Sales)
- "Job Work Charges" in expense section → Row 46 (Manufacturing cost)
- "TDS" in Subnotes to BS (asset side) → Row 221 (Advance Income Tax paid BY company)
- "TDS" in statutory dues (liability side) → Row 246 (Tax owed BY company)

The item text alone is INSUFFICIENT. The (sheet_name, section, raw_text) triple is the true input.

### 2c. Inter-annotator disagreement (different CAs classify differently)
Different qualified CAs make different professional judgment calls on ~15-20% of items:
- "Bad Debts Written Back" → Row 34 (Other Non-Operating Income) at Company A, Row 69 (Bad Debts reversal) at Company B
- "Rates & Taxes" → Row 68 (Rent, Rates and Taxes) at Company A, Row 71 (Others Admin) at Company B
- "Directors Remuneration" → Row 67 (Salary) at Company A, Row 73 (Audit Fees & Directors Remuneration) at Company B

There is no single "correct" answer for these items — it depends on the CA's interpretation and the company's accounting policy.

### 2d. Industry-specific patterns
- Manufacturing: has Wages (R45), Job Work (R46), Manufacturing Depreciation (R56), Stock-in-Process (R53/54)
- Trading: has Purchase of Goods for Resale (R42), no manufacturing rows
- Partnership: has Partners' Capital (R116), Partners' Salary (R73), Interest to Partners (R83)
- Services: different expense structure entirely

A model that works for manufacturing may fail on trading or partnership companies.

### 2e. Sparse reference data
- The authoritative CMA reference mapping has 384 entries covering 139 rows
- Many CMA rows have only 1-2 example descriptions
- No large-scale labeled dataset exists for Indian CMA classification
- Creating ground truth requires expensive CA labor

---

## 3. Tech Stack

- **Backend:** Python FastAPI + Supabase + ARQ (Redis task queue)
- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Database:** PostgreSQL via Supabase (Auth + Storage + RLS)
- **AI Classification:** Claude Haiku 4.5 (via OpenRouter API)
- **OCR:** Surya-OCR for scanned PDFs
- **Containerization:** Docker Compose (backend + frontend + redis)

---

## 4. Current Classification Architecture

The system uses a **4-tier pipeline** (in `backend/app/services/classification/pipeline.py`):

```
Tier 0: Deterministic Rule Engine (61 regex rules, 1,021 lines)
   ↓ (if no match)
Tier 1: Fuzzy String Matching (against 384-item CMA reference + learned_mappings)
   ↓ (if score < 85)
Tier 2: Claude Haiku AI Classification (LLM prompt with 139 fields + disambiguation rules)
   ↓ (if confidence < 0.8 or uncertain)
Tier 3: Doubt Report (flagged for human CA review)
```

### Tier 0 — Rule Engine (`rule_engine.py`)
- 61 deterministic pattern-matching rules from 7-company analysis
- Patterns like: `r"(?i)\bdirectors?\s*remuneration"` → Row 67
- 9-phase priority ordering (absolute rules first, context-dependent last)
- **Accuracy: 100% on matched items (by definition)**
- **Problem: Only fires on items with exact/similar wording to the 7 test companies. New client terminology won't match.**

### Tier 1 — Fuzzy Matcher (`fuzzy_matcher.py`)
- Uses `thefuzz` library (Levenshtein distance) against:
  - `learned_mappings`: CA-corrected items from past runs (checked FIRST)
  - `reference_mappings`: 384-item CMA reference (authoritative)
- Threshold: score >= 85 → auto-classify
- **Problem: Fails on semantic similarity. "Statutory Remittances Pending" won't fuzzy-match "ESI Payable" (completely different words).**

### Tier 2 — AI Classifier (`ai_classifier.py`)
- Sends to Claude Haiku via OpenRouter API
- Prompt includes: all 139 CMA fields (grouped by category) + ~50 disambiguation rules + sheet/section context
- **This is where the accuracy problem lives.**
- Current prompt: ~300 lines, ~3,500 input tokens per call

### Tier 3 — Doubt Report
- Items where Haiku confidence < 0.8 or it explicitly flags uncertainty
- Shown to CA in a filtered review page
- CA corrections feed into `learned_mappings` for future runs

### Additional features:
- Auto-approve threshold: items with confidence >= 0.85 are silently approved
- Review page filter: shows only "needs_review" items by default (toggle to show all)
- Trial Balance sheets are auto-excluded from extraction

---

## 5. What We've Tried and Results

### Attempt 1: Baseline Prompt (Zero-Shot)
**Date:** 2026-03-23
**Approach:** Send all 139 CMA fields as a flat list to Haiku with basic instructions.
**Result:** **78.4% accuracy** on BCIPL (276/352 unique items)
**Failure patterns:** Adjacent field confusion (48.7%), depreciation routing (10.5%), loan classification (9.2%)

### Attempt 2: Prompt Tuning with AI Self-Diagnosis
**Date:** 2026-03-23
**Approach:** 7-phase structured experiment:
1. Created ground truth for BCIPL (448 items, manually cross-referenced against CA's CMA output)
2. Ran baseline, analyzed all 76 failures
3. "Interviewed" Haiku about its mistakes (asked why it chose wrong answers)
4. Generated disambiguation rules from interviews
5. Grouped CMA fields into 14 categories (structural improvement)
6. Added 3-step routing (Sheet → Section → Description)
7. Tested revised prompt

**Result:** **92.0% accuracy** on BCIPL-specific prompt (+13.6pp)
- Recovered 62/77 baseline failures (80.5% recovery)
- **But introduced 13 regressions** (items that were correct before, now wrong)
- Key insight: AI self-diagnosis finds problems but doesn't reliably solve them

### Attempt 3: Genericized Prompt (removed company-specific rules)
**Date:** 2026-03-23
**Approach:** Made the BCIPL-specific prompt generic for any company. Removed hardcoded company names, split rules into Universal / Manufacturing / Trading / Partnership sections.
**Result:** **87.4% accuracy** on BCIPL (-4.6pp from company-specific)
- Lost BCIPL-specific rules that were "load-bearing"
- 44 errors, distributed across 9 failure patterns
- Report recommended 5 "must-add" rules claiming they'd recover ~30 of 44 errors → "~96%"

### Attempt 4: Added the 5 "must-add" rules to generic prompt
**Date:** 2026-03-24
**Approach:** Added the 5 recommended rules (statutory liabilities, job work revenue, wages vs salary, sellers credit, TDS in BS) to the generic prompt.
**Result:** NOT RE-TESTED — but based on the loop pattern from Attempts 2→3, adding rules fixes known errors and introduces new regressions. The user correctly identified this as a **dead-end loop**:

```
Test → 87% → "add 5 rules → ~96%" → Test → 87% → "add 5 rules → ~96%" → ...
```

**Key learning:** Prompt-based classification has a ceiling at ~87-92%. Adding more disambiguation rules to the prompt fixes known errors but introduces new regressions. The prompt becomes contradictory as it grows. This is a prompt engineering dead end.

### Attempt 5: Rule Engine V2 (61 deterministic rules)
**Date:** 2026-03-23
**Approach:** Implemented 35+ new classification rules from 7-company analysis into the Tier 0 rule engine. Rules are regex patterns that fire deterministically before fuzzy match or AI.
**Result:** 100% accuracy on matched items (by definition), 11/11 smoke test items correct.
**Problem:** Rules are overfitted to the 7 test companies' exact wording. "Directors Remuneration" matches, but "Remuneration to Directors" or "KMP Compensation" would not. A new client's financial statements will use different terminology.

### Attempt 6: RAC Phase 1 — Retrieval Augmented Classification (cross-industry)
**Date:** 2026-03-23
**Approach:** Embed SR Papers (216 trading items) as a vector database. For each BCIPL item (manufacturing), find the 5 most similar items via cosine similarity, narrow to candidate CMA fields, send to Haiku with examples instead of rules.
**Embedding model:** all-MiniLM-L6-v2 (sentence-transformers, local, free)
**Result:** **79.0% projected accuracy**
- Embedding-only top-1 accuracy: 21.2%
- Haiku recovery on hard cases: 73.3% (when correct field was in candidates)
- Haiku accuracy on easy cases: 90.0%
- **Co./Deprn sheet: 2.5% accuracy** (SR Papers has no depreciation schedule — zero relevant examples to retrieve)

**Key learning:** Cross-industry retrieval is too hard. Trading company data can't classify manufacturing items. But Haiku's reasoning is sound when given the right candidates — the bottleneck is retrieval quality.

### Attempt 7: RAC Phase 2 — 6-company database (multi-industry)
**Date:** 2026-03-24
**Approach:** Built ground truth for 5 more companies (total 7 companies, 1,455 items). Used 6 companies (1,007 items) as database, held out BCIPL (448 items) as test.
**Result:** **63.6% projected accuracy** ← WORSE than Phase 1 with less data!

| Metric | Phase 1 (216 items, 1 company) | Phase 2 (1,007 items, 6 companies) |
|--------|-------------------------------|-------------------------------------|
| Embedding top-1 | 21.2% | 44.4% |
| Embedding top-10 recall | Not measured | 72.3% |
| RAC projected | 79.0% | 63.6% |

**Why more data made it WORSE:**
1. **Inter-annotator disagreement:** Different CAs at different companies classified identical items into different CMA rows. The retriever now pulls back CONFLICTING examples (e.g., "Bad Debts Written Back" → Row 34 from Company A, Row 69 from Company B), confusing Haiku.
2. **Embedding recall ceiling:** For 27.7% of BCIPL items, the correct CMA row doesn't appear anywhere in the top-10 retrieved candidates. Haiku literally cannot pick the right answer.
3. **Section label noise:** OCR-extracted section labels differ across companies, causing semantic mismatches in the context strings used for embedding.

**This was the critical finding:** RAC using other companies' classified data as the retrieval database is fundamentally flawed because of inter-annotator disagreement. More data from more CAs = more conflicting labels = worse performance.

---

## 6. Summary of All Results

| Attempt | Approach | Accuracy | vs Baseline |
|---------|----------|----------|-------------|
| 1 | Zero-shot prompt (flat 139 fields) | 78.4% | — |
| 2 | Tuned prompt (BCIPL-specific) | 92.0% | +13.6pp |
| 3 | Generic prompt (universal rules) | 87.4% | +9.0pp |
| 4 | Generic + 5 must-add rules | ~87-92% (loop) | Dead end |
| 5 | Rule Engine V2 (61 regex rules) | 100% on matched | Overfitted |
| 6 | RAC Phase 1 (1 company DB, cross-industry) | 79.0% | -8.4pp |
| 7 | RAC Phase 2 (6 company DB, multi-industry) | 63.6% | -23.8pp |

---

## 7. What We Know Works

1. **Context matters more than rules:** Grouping 139 fields into 14 categories and adding 3-step routing (Sheet → Section → Description) was the single biggest improvement (78.4% → 92.0%). Structure > instructions.

2. **Haiku's reasoning is strong when focused:** When given 4-8 candidate fields instead of 139, Haiku achieves 90% accuracy on easy cases and 73% recovery on hard cases. The problem is giving it the RIGHT candidates.

3. **Sheet + section context eliminates 80%+ of wrong answers for free:** If sheet = "Notes to P & L", the answer MUST be rows 22-108. If section = "employee benefits", it's rows 45/67/73. This is deterministic and costs nothing.

4. **The 384-item CMA reference is the authoritative knowledge source:** It has one consistent interpretation per item (no CA disagreement). The prompt approach works because it uses this reference. The RAC approach failed partly because it used conflicting multi-CA data instead.

5. **Auto-approve at 85%+ confidence works well:** Reduces CA review queue from ~700 items to ~100. The review UX is already built.

6. **Fuzzy matching handles exact/near-exact duplicates:** When a previous client used the same wording, `learned_mappings` catches it perfectly. But it can't handle semantic similarity.

---

## 8. What Doesn't Work

1. **Adding more rules to the prompt:** Every rule added risks regressions elsewhere. The prompt grows contradictory. Dead-end loop confirmed.

2. **Regex rule engine for generalization:** Rules match exact patterns from test companies. New terminology won't fire them.

3. **RAC with multi-CA ground truth as the retrieval database:** Inter-annotator disagreement means more data = more conflicting examples = worse accuracy. Fundamentally flawed data source.

4. **Embedding-only classification (no LLM):** Top-1 accuracy maxes out at 44% even with 1,007 items. Embeddings alone can't handle the nuance.

5. **AI self-diagnosis for generating rules:** Haiku interviews find problems but propose wrong solutions. 13 regressions came from "fixes" Haiku suggested.

---

## 9. Data Assets Available

### Ground Truth (classified items with verified CMA row):
| Company | Industry | Items | CMA Rows | File |
|---------|----------|-------|----------|------|
| BCIPL | Manufacturing (metal stamping) | 448 | 64 | `DOCS/extractions/BCIPL_classification_ground_truth.json` |
| SR Papers | Trading (paper distribution) | 216 | 33 | `DOCS/extractions/SR_Papers_classification_ground_truth.json` |
| SSSS | Trading (steel distribution) | 294 | 44 | `DOCS/extractions/SSSS_classification_ground_truth.json` |
| MSL | Manufacturing (metal stamping) | 110 | 50 | `DOCS/extractions/MSL_classification_ground_truth.json` |
| SLIPL | Manufacturing (shoe) | 65 | 39 | `DOCS/extractions/SLIPL_classification_ground_truth.json` |
| INPL | Manufacturing (nano/bio) | 186 | 63 | `DOCS/extractions/INPL_classification_ground_truth.json` |
| Kurunji Retail | Partnership (retail) | 136 | 33 | `DOCS/extractions/Kurunji_Retail_classification_ground_truth.json` |
| **TOTAL** | **3 industries** | **1,455** | **88 unique** | |

### Ground truth format (JSON array):
```json
{
  "raw_text": "ESI payable",
  "amount_rupees": 342000,
  "financial_year": 2023,
  "section": "other current liabilities",
  "sheet_name": "Notes BS (2)",
  "correct_cma_field": "Other statutory liabilities (due within 1 year)",
  "correct_cma_row": 246,
  "confidence_note": "verified",
  "reasoning": "ESI is a statutory employee obligation"
}
```

### Other reference data:
- `DOCS/CMA classification.xls` — 384-item authoritative CMA reference mapping (one interpretation per item)
- `DOCS/CMA.xlsm` — CMA Excel template with macros (the output format)
- `DOCS/rules/*.md` — 7 company-specific classification rule files (119 rules total, 85-90 unique)
- `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/generic_prompt_template.txt` — Current best prompt (300 lines)
- `DOCS/test-results/bcipl/prompt-tuning-2026-03-23/FINAL_REPORT.md` — Full prompt tuning experiment report

### Embeddings:
- `DOCS/test-results/rac-phase1/embeddings.npz` — Phase 1 embeddings (all-MiniLM-L6-v2)
- `DOCS/test-results/rac-phase2/embeddings_phase2.npz` — Phase 2 embeddings (all-MiniLM-L6-v2)

---

## 10. Constraints

- **No fine-tuning:** We don't have ML infrastructure for training custom models. Solution must use off-the-shelf models or APIs.
- **Cost-sensitive:** User is on Claude Max (unlimited Haiku subagent calls in Claude Code). Production uses OpenRouter API (~$0.19 per company for Haiku). Solution should not significantly increase per-company cost.
- **No client dependency:** The system must be accurate from day 1 for new clients. Cannot rely on client data to train/improve the model.
- **Indian accounting domain:** All financial statements are Indian companies following Indian Accounting Standards (Ind AS) or old Indian GAAP. CMA is an Indian banking requirement.
- **Macro preservation:** The output CMA Excel must keep VBA macros intact (keep_vba=True, .xlsm format).
- **V1 scope:** Historical data only, no projections. Fills INPUT SHEET + TL Sheet only.

---

## 11. The Goal

Build a classification system that:

1. **Achieves >93% accuracy** on any new Indian company's financial statements without company-specific rules or training
2. **Uses (sheet_name, section, raw_text, industry_type) as combined input** — not just the item text
3. **Handles new terminology** without explicit regex patterns (semantic understanding, not string matching)
4. **Uses the 384-item CMA reference as the authoritative mapping** — this is the single source of truth with no inter-annotator disagreement
5. **Does not degrade as it scales** — no prompt length regression, no rule conflicts
6. **Works across industries** (manufacturing, trading, partnership, services) without industry-specific rule sets
7. **Improves over time** as more companies are processed — CA corrections should make it better, not worse
8. **Keeps cost low** — ideally cheaper than the current $0.19/company
9. **Integrates with the existing 4-tier pipeline** — can replace or augment Tier 2 (AI classifier) without changing Tier 0/1/3

---

## 12. Open Questions for a Solution

1. How do we leverage the 384-item CMA reference (authoritative, no disagreement) as the primary knowledge source while still benefiting from the 1,455 classified examples (which have disagreement)?

2. Is there an approach that uses embeddings to narrow candidates from the 384-item reference (not from multi-CA data), combined with context filtering (sheet/section), to give Haiku a short, focused prompt?

3. Can hierarchical classification (first classify into 14 category groups, then into specific CMA row within the group) break through the 87-92% ceiling?

4. Would a finance-domain embedding model (FinBERT, Fin-E5) perform significantly better than all-MiniLM-L6-v2 for Indian accounting text similarity?

5. Is there a way to handle inter-annotator disagreement constructively — e.g., detecting when multiple valid mappings exist and presenting both to the CA?

6. Would a two-model approach work — one model for candidate generation (cheap, fast) and another for final classification (more expensive, accurate)?

---

*Document generated: 2026-03-24 | Full classification problem context for solution exploration*
