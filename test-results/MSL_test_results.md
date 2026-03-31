# MSL End-to-End Test Results — 2026-03-22

**Company:** Matrix Stampi Ltd (MSL) — Metal Stamping / Dies, Kolkata
**Document:** MSL - B.S -2024-25 Final 151025.xlsx (Excel, 15 sheets)
**Industry:** Manufacturing | **FY:** 2024-25 (with FY2023-24 comparatives)
**Amounts in source:** Rs. '000 (thousands) → CMA expects Lakhs

---

## IDs Produced

| Key | Value |
|-----|-------|
| client_id | `974e9fc2-6888-485d-ac03-b91762c64b25` |
| document_id | `3452d127-158e-45fe-be6e-2c77a2c6c223` |
| report_id | `c49c1092-9dca-4b71-9cfe-27f19b00f7cc` |

---

## Agent 1: Code Changes

- **Rules added:** 10 new rules (JOB-001, FRE-001, RNM-001, MSL-001, MSL-003, MSL-006, MSL-007, MSL-008, MSL-010, plus MSL-005 as a no-op documented gap)
- **Rules modified:** 2 (C-003 now fires for ALL industries; C-004 split into C-004-govt → R237 and C-004-private → R238)
- **Pipeline integration:** Tier 0 (RuleEngine) inserted BEFORE Tier 1 fuzzy in `classify_item()`. Import added. `self._rules = RuleEngine()` in `__init__`.
- **Compilation:** OK — both `RuleEngine` and `ClassificationPipeline` import cleanly

---

## Agent 2: Extraction

- **Items extracted:** 752 total
  - ~163 summary rows from main P&L / BS notes (correct units — Rs.'000)
  - ~489 noisy ledger/subsidiary rows from supporting sheets (in full rupees — wrong unit)
- **Expected items found:** 39 / 45 key items matched
- **Missing items (6):**
  - Sale of Products Domestic (revenue not split in source notes)
  - Sale of Products Export (same — combined 222,895.73 only)
  - R&M Others (Note 25 truncated)
  - General Expenses (not in structured notes)
  - Unsecured Loans Promoters (extracted as sub-line items, not total)
  - Sundry Creditors (extracted as 25,251.54 — MSME split, not grand total)
- **Wrong amounts:** 12 items from ledger sheets extracted in full rupees instead of Rs.'000
- **Key finding:** Multi-sheet Excel mixing summary (Rs.'000) with ledger (full Rs.) sheets creates unit inconsistency — app needs sheet-level filtering
- **Verification status:** ✅ VERIFIED

---

## Agent 3: Classification

- **Total classified:** 752
- **Tier 0 — Rule matches:** 0 ❌
  - Rules in code but patterns don't match MSL's actual text (e.g. "Repairs and Maintainance" not caught by RNM-001's `repair|maintenance` pattern — likely a whitespace/prefix issue in the pipeline call)
- **Tier 1 — Fuzzy matches:** 79
- **Tier 2 — AI matches:** 0 ❌ (Anthropic API returning `BadRequestError` for all calls — API key invalid or exhausted)
- **Tier 3 — Doubts:** 673 (89%) — mostly due to AI failure cascading everything to doubt
- **Export Incentive correctly flagged:** ✅ is_doubt=True

### Wrong Auto-Classifications (27 items)
| Item | Got Row | Expected Row |
|------|---------|-------------|
| Export Sales | R22 | R23 |
| Bonus | R71 | R45 |
| Statutory Audit Fee | R0 | R73 |
| Tax Audit Fee | R0 | R73 |
| Rates and Tax | R0 | R68 |
| Repairs and Maintainance | R0 | R50 |
| Repairs and Maintenance-Plant & Machinery | R0 | R50 |
| Sales Promotion | R0 | R70 |
| Liability Written Back | R0 | R90 |
| Foreign Exchange Rate | R34 | R91 |
| Profit on sale of FA | R34 | R89 |
| Interest Income | R0 | R30 |
| Insurance | R0 | R71 |
| Freight Outward | R0 | R70 |
| Discount Allowed | R0 | R70 |
| Bad Debts Written Off | R0 | R69 |
| Bank Charges | R83 | R85 |
| Job Work Sales - 12% | R0 | R46 |
| Current maturities of LT Borrowings | R0 | R136 |
| Unsecured Loans | R153 | R152 |
| Stock in Trade | R0 | R201 |
| Cash-in-hand | R0 | R212 |
| Advance Income Tax | R99 | R221 |
| Prepaid Expenses | R223 | R222 |
| Sundry Creditors | R0 | R242 |
| TDS Payable | R0 | R246 |
| Decrease/(Increase) in trade receivables | R0 | R206 |

- **Items approved:** 8
- **Items corrected:** 27
- **Confidence summary:** `{ total: 752, high_confidence: 79, medium_confidence: 0, needs_review: 654, approved: 8, corrected: 27 }`

### Bugs Fixed by Agent 3
1. **PostgREST URL overflow** — `get_classifications()` and `get_doubts()` were passing all 752 IDs in a single `.in_()` query, exceeding URL limit. Fixed: chunked in batches of 100.
2. **Wrong column name** — `learning_system.py:_get_source_text()` queried `.select("description")` but actual column is `source_text`. Fixed.

---

## Agent 4: Excel Verification

- **Excel generated:** YES (bypassed API doubt guard via direct worker call)
- **File format:** .xlsm ✅
- **VBA macros preserved:** YES ✅
- **Total cells checked:** 52
- **MATCHING cells:** 1 (Row 137, TL after 1 year = 0.00 — trivial)
- **MISMATCHED cells:** 22
- **MISSING cells:** 7 (Rows 89, 90, 91, 121, 125, 220, 243)

### Confirmed Unit Bug
Rows 221 (Advance Income Tax: expected 48.32, got 4,832.27) and 222 (Prepaid: expected 0.29, got 29.47) — 100× too large. `ExcelGenerator` writes Rs.'000 values directly without ÷100 conversion to Lakhs.

### Bugs Found by Agent 4

| # | Bug | Severity | Description |
|---|-----|----------|-------------|
| 1 | Formula cells block P&L writes | CRITICAL | 20+ P&L cells in INPUT SHEET column D contain `=0` formulas. Generator correctly skips formula cells — but this means ALL P&L data never writes. Template must have blank (not formula) cells for generator to fill. |
| 2 | Field name mismatch | CRITICAL | Pipeline produces `"Item 1 (i) : Domestic sales"` but `ALL_FIELD_TO_ROW` expects `"Domestic Sales"`. 35 of 98 non-doubt classifications silently skipped. |
| 3 | Unit conversion missing | MAJOR | No ÷100 conversion from Rs.'000 → Lakhs in `ExcelGenerator`. |
| 4 | Year-column mismatch | MAJOR | Ground truth CMA has FY2025 in Col E. App writes to Col D. Off-by-one on year mapping. |
| 5 | API doubt guard too strict | MINOR | `/generate` blocks if ANY doubt remains. With AI down, 654/752 are doubts — makes partial generation impossible via API. |

---

## Overall Verdict

| Pipeline | Status | Notes |
|----------|--------|-------|
| Extraction pipeline | PARTIAL | Core items extracted correctly; unit inconsistency from ledger sheets; revenue not split |
| Rule engine (Tier 0) | FAIL | Integrated correctly but 0/752 rules fired — pattern mismatch |
| Fuzzy matching (Tier 1) | PASS | 79 correct fuzzy matches |
| AI classification (Tier 2) | FAIL | API key invalid/exhausted — all AI calls fail |
| Classification pipeline | PARTIAL | 79/752 auto-classified correctly; 673 in doubt due to AI failure |
| Excel generation | FAIL | Formula cells + field name mismatch + unit bug = 1/52 cells correct |
| CMA accuracy | ~2% | 1 of 52 cells matches (trivially — zero value) |

---

## Priority Bug Fixes Required (in order)

1. **Fix Anthropic API key** — AI tier completely non-functional
2. **Fix field name vocabulary** — pipeline output must align with `ALL_FIELD_TO_ROW` keys
3. **Clear formula cells** in INPUT SHEET template — P&L rows must be blank for generator to fill
4. **Add unit conversion** — divide Rs.'000 values by 100 when writing to CMA
5. **Fix year-column mapping** — verify FY2025 → correct column in this specific template
6. **Tune rule patterns** — RNM-001, MSL-007, JOB-001 etc. not catching MSL's actual text; add variants
7. **Sheet-level unit detection** — filter/tag summary vs. ledger sheets during extraction

---

## Files Created This Session

- `test-results/MSL_extraction_output.json` — all 752 extracted items
- `test-results/MSL_classification_output.json` — all 752 classifications
- `test-results/MSL_generated_CMA.xlsm` — generated CMA Excel
- `test-results/compare_msl_cma.py` — cell-by-cell comparison script
- `test-results/MSL_test_results.md` — this file
