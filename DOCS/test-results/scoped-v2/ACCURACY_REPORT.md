# Scoped Classification v2 — Accuracy Report

Generated: 2026-03-26
Ground truth: BCIPL (448 items)
Benchmark script: `backend/run_bcipl_full.py`
Elapsed: 1158s (Phase 1) + ~360s (Phase 3 interrogation)

---

## Overall Metrics

| Metric | Value | Baseline | Delta |
|--------|-------|----------|-------|
| Overall accuracy | **62.7%** | 87% | **-24.3pp** |
| Doubt rate | 5.4% | 13% | -7.6pp |
| Accuracy within classified | 66.3% | — | — |
| Wrong items | 143 | — | — |
| Doubt items | 24 | — | — |

**PASS/FAIL:**
- Overall accuracy > 90%: ❌ FAIL (62.7%)
- Doubt rate < 10%: ✅ PASS (5.4%)
- Acc within classified > 95%: ❌ FAIL (66.3%)

---

## Error Categories

| Category | Count | % of errors | Fix |
|----------|-------|-------------|-----|
| Confident wrong — both models agreed on wrong row | 131 | 92% | Section routing + context fix |
| Debate wrong — debated but still wrong | 12 | 8% | Better debate prompt |
| Single-model wrong | 0 | 0% | — |

**Key insight:** 92% of wrong answers had BOTH models agree confidently — this is NOT a debate/doubt issue. The models are consistently wrong because they are shown the wrong set of rows (routing bug).

---

## Section Routing Analysis

| Section | Total | Correct | Accuracy | Wrong | Doubt |
|---------|-------|---------|----------|-------|-------|
| `investments` | 1 | 0 | 0.0% | 1 | 0 |
| `admin_expense` | 90 | 20 | **22.2%** | 59 | 11 |
| `borrowings_short` | 4 | 1 | 25.0% | 3 | 0 |
| `tax` | 10 | 3 | 30.0% | 6 | 1 |
| `selling_expense` | 9 | 3 | 33.3% | 5 | 1 |
| `employee_cost` | 37 | 20 | 54.1% | 15 | 2 |
| `depreciation` | 18 | 10 | 55.6% | 8 | 0 |
| `other_assets` | 43 | 24 | 55.8% | 19 | 0 |
| `manufacturing_expense` | 6 | 4 | 66.7% | 2 | 0 |
| `finance_cost` | 20 | 14 | 70.0% | 5 | 1 |

### "other expenses" routing:
- 25 items with section text containing "other expenses"
- **All 25 routed to `admin_expense`** (routing fallback)
- Correct rows for these 25 items include: Row 44, 46, 48, 49 (manufacturing rows), Row 84, 85, 91 (finance rows) — **none present in admin_expense context**

---

## Root Cause Analysis (from Phase 3 model interrogation)

30 confident-wrong items interrogated via OpenRouter (DeepSeek V3 + Gemini Flash).

### Root Cause 1: Correct row NOT in scoped context (53% of interrogated errors)

**Items:** Consumption of Stores & Spares, Job Work Charges, Power & Fuel, Bill Discounting Charges, Bank Charges, Forex Rate Fluctuation Loss, Brought forward P&L, Axis Bank Channel Financing, Inland LC Discounting, Capital Work-In-Progress, MAT Credit Entitlement, Unsecured non-current receivable, Advance to Suppliers, Other Advances, Advance From Customers, Leave Encashment (Short-term Provision)

**Both models consistently said:** *"Row X was not in the list you showed me."*

**Specific example (DeepSeek V3 on "Consumption of Stores & Spares"):**
> "The prompt only provided a limited set of CMA rows to choose from, and Row 44 was not included. The examples from other companies mentioned Row 44, but it wasn't an available option in the classification task."

**Specific example (Gemini Flash on "Job Work Charges"):**
> "The correct answer was not in the list of possible rows."

**Fix:** Fix section routing for `"other expenses"` → should NOT default to `admin_expense`. Manufacturing items (`power & fuel`, `job work`, `stores & spares`) need `manufacturing_expense` context.

---

### Root Cause 2: Cross-section examples contaminate the context (critical insight)

**Gemini Flash on "Manufacturing Expenses" (item 6):**
> *"The prompt contained two different lists of POSSIBLE CMA ROWS. The first list (Rows 67–77) was used for the classification. The second list (Rows 44–71) was only used in the EXAMPLES FROM OTHER COMPANIES section. I incorrectly assumed that the examples were using the same list of rows as the classification task."*

This is a **structural prompt bug**: the `admin_expense` context's EXAMPLES section references Row 44, 46, 48, 49 (manufacturing rows). When models see these in examples but not in the "pick from these" list, they get confused and default to Row 71 ("Others").

**Fix:** Filter training examples to only include rows that are in the current context's CMA rows list.

---

### Root Cause 3: Wrong/misleading training example in ground truth

**DeepSeek V3 on "Directors Remuneration" (item 3):**
> *"The example provided in the prompt explicitly stated: 'Directors Remuneration' → Row 73 (Audit Fees & Directors Remuneration). This example directly influenced my decision. The correct answer is Row 67."*

There is a corrupted training example mapping "Directors Remuneration" → Row 73 when the correct mapping is Row 67.

**Fix:** Audit and correct the training data — remove/fix the `"Directors Remuneration" → Row 73` example.

---

### Root Cause 4: Two CMA rows share the same name "Depreciation" (Row 56 vs Row 63)

**Both models on "Depreciation" and "Amortization Expenses":**
> DeepSeek V3: *"Both Row 56 and Row 63 were labeled 'Depreciation'. I didn't carefully check the codes."*
> Gemini Flash: *"The prompt included two rows with the exact same name. This made it unclear which one was correct."*

The depreciation context shows both Row 56 (Depreciation, code II_C14) and Row 63 (Depreciation, code II_C20) with identical names.

**Fix:** Rename the rows to distinguish them — e.g., "Depreciation (Manufacturing)" vs "Depreciation (Admin)" or use the actual CMA code as the differentiator in the prompt.

---

### Root Cause 5: Overly broad rule causes wrong classification

**DeepSeek V3 on "Machinery Maintenance" (item 7):**
> *"Tunnel vision on 'Maintenance' → saw 'Repairs & Maintenance' and stopped evaluating. The example 'Building Maintenance → Repairs' misled me to generalize all maintenance."*

**Gemini Flash on "Packing Materials":**
> *"The rule 'Packing charges → Row 71 (Others)' was too general and didn't account for packing materials specifically used for sales and distribution."*

Rules that are too broad (matching on single words like "maintenance", "packing") override correct classification.

**Fix:** Make rules more specific — "Building Maintenance → Row 72" not "Maintenance → Row 72". Add: "Packing materials (sales) → Row 70", "Machinery Maintenance → Row 49 (Others Manufacturing)".

---

## Model Self-Diagnosis Pattern Summary

| Pattern | DeepSeek V3 | Gemini Flash | Interpretation |
|---------|-------------|--------------|----------------|
| Correct row not in list | 12 | 10 | Section routing bug |
| Defaulted to "Others" | 7 | 0 | Row not available → fallback |
| Ambiguous item text | 6 | 4 | Need disambiguation rules |
| Conflicting examples | 0 | 2 | Bad training examples |
| Model reasoning error | 20 | 7 | Broad rules, same-name rows |

---

## Recommended Fixes (prioritized by impact)

### Fix 1 — Section router: "other expenses" → split routing (HIGHEST IMPACT)
**Affects:** ~25+ items, ~15+ wrong items
The regex `other expense` → `admin_expense` is wrong. "Other expenses" in Indian P&Ls is a catch-all that contains both manufacturing AND admin items. The router must detect manufacturing sub-items and route them to `manufacturing_expense` context.

**Action:** Add keywords to the manufacturing_expense route pattern:
- "power", "fuel", "job work", "contract labour", "stores", "spares consumed" should route to `manufacturing_expense` even when the section says "other expenses"

### Fix 2 — Filter cross-section examples from scoped context (HIGH IMPACT)
**Affects:** All sections, most confident-wrong items
The `_build_scoped_contexts()` function includes training examples from all companies. These examples reference rows from OTHER sections. When models see Row 44 in examples but not in the "pick from these" list, they get confused.

**Action:** In `_build_scoped_contexts()`, filter training examples to only include ones where `example['label']` is in the current context's `cma_rows` list.

### Fix 3 — Fix the "Directors Remuneration → Row 73" training example (MEDIUM IMPACT)
**Affects:** All `employee_cost` routed items that look like directors remuneration
A corrupted example is actively misleading both models.

**Action:** Find and fix/remove the training example mapping Directors Remuneration to Row 73.

### Fix 4 — Rename duplicate "Depreciation" rows in context (MEDIUM IMPACT)
**Affects:** All `depreciation` section items (~18 items, ~8 wrong)
Row 56 and Row 63 both show as "Depreciation" in the prompt.

**Action:** In `_build_prompt()`, when building `rows_text`, append the section name or sub-category to disambiguate identically-named rows.

### Fix 5 — Add section-specific disambiguation rules (MEDIUM IMPACT)
**Affects:** `selling_expense`, `admin_expense` sections
Rules like "Packing charges → Others" are too broad.

**Action:** Add specific rules:
- "Packing materials (in selling context) → Row 70 (Advertisements and Sales Promotions)"
- "Machinery Maintenance → Row 49 (Others Manufacturing)"
- "Rates & Taxes (admin context) → Row 71 (Others Admin), NOT Row 68 (Rent, Rates and Taxes)"

### Fix 6 — Fix balance sheet items routing (MEDIUM IMPACT)
**Affects:** Items 18-30 in interrogation (Row 106, 131, 132, 136, 165, 220, 236, 238, 243, 244, 250)
Balance sheet items like "Capital Work-In-Progress", "MAT Credit", "Advance From Customers" are routed to `admin_expense` context and their correct rows don't exist there.

**Action:** Review section routing for balance sheet sections (appropriation, other_assets, current_liabilities, fixed_assets) to ensure correct context is selected.

---

## Files

| File | Location |
|------|----------|
| Phase 1 raw results | `DOCS/test-results/scoped-v2/accuracy_results.json` |
| Phase 3 interrogation | `DOCS/test-results/scoped-v2/model_interrogation.json` |
| This report | `DOCS/test-results/scoped-v2/ACCURACY_REPORT.md` |

---
*Benchmark: `backend/run_bcipl_full.py`. 448 items tested. 60 OpenRouter API calls (Phase 3).*
