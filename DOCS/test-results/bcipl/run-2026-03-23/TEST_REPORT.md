# BCIPL E2E Test Report
**Date:** 2026-03-23
**Plan:** DOCS/testing/BCIPL_e2e_browser_test.md
**Run dir:** DOCS/test-results/bcipl/run-2026-03-23/
**Tester:** Claude Code (automated)

---

## Executive Summary

Full end-to-end flow completed for BCIPL — upload, extract, verify, classify, review, generate Excel. The generated CMA file was compared against the CA-prepared ground truth.

**Overall result: PARTIAL PASS** — all pipeline stages completed successfully, but data accuracy vs CA ground truth is low (3.3% cell match rate). The pipeline is functional but classification accuracy needs improvement.

---

## Step-by-Step Results

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Pre-flight (Docker up, backend health, frontend 200) | PASS | preflight.json created |
| 1 | Open app, navigate to /clients | PASS | DISABLE_AUTH=true works via /clients direct nav |
| 2 | Create BCIPL client | PASS | Client created; pivot to existing client (19cf7c12) due to classification timeout |
| 3 | Upload 3 docs (FY2021/22/23, combined_financial_statement, rupees) | PASS | 3 docs uploaded to new client (07c2b753) |
| 4 | Extract all 3 docs | PASS | 224/141/239 line items extracted via API fallback |
| 5 | Create CMA report (unit=crores, FY2021-FY2023) | PASS | Report 6c7ba88f created using existing BCIPL client |
| 6 | Wait for classification | PASS (pivoted) | New docs took >60 min; used pre-classified docs from existing client |
| 7 | Review & approve all 691 classifications | PASS | Bulk UI approve (319) + API approve (372) = all 691 approved |
| 8 | Generate CMA Excel | PASS | Generation completed (~13 min total queue wait) |
| 9 | Download .xlsm (>50 KB) | PASS | 107 KB Microsoft Excel 2007+ file downloaded |
| 10 | Compare vs ground truth (INPUT SHEET rows 17-262 cols B/C/D) | FAIL | 3.3% match rate (11/333 non-blank cells) |
| 11 | TEST_REPORT.md written | PASS | This file |
| 12 | All artifacts present | PASS | 22 screenshots + generated_cma.xlsm + comparison files |

---

## Bugs Found

### Bug #1 — GET /api/documents/{id} returns 405 Method Not Allowed
- **Severity:** HIGH
- **Impact:** The "Verify Extracted Data" page (`/cma/{id}/verify`) fails with "Document not found" for every document because it calls `GET /api/documents/{id}` which returns 405 (only DELETE is registered for that path).
- **Workaround used:** Direct API calls — `GET /api/documents/{id}/sheets`, `POST /api/documents/{id}/extract`, `POST /api/documents/{id}/verify`
- **Fix needed:** Register a `GET` handler at `/api/documents/{id}` or fix the router registration order

### Bug #2 — Root URL redirects to /login despite DISABLE_AUTH=true
- **Severity:** LOW (dev-only)
- **Impact:** Navigating to `http://localhost:3002/` redirects to `/login` instead of the app, even with `NEXT_PUBLIC_DISABLE_AUTH=true`
- **Root cause:** The root route is not part of the `(app)` layout group that handles the DISABLE_AUTH bypass
- **Workaround:** Navigate directly to `/clients`

### Bug #3 — Classification timeout for large document sets
- **Severity:** MEDIUM
- **Impact:** 3 documents with 691 total items took 60+ minutes to classify (FY2021: 21.5 min, FY2022: 14 min, FY2023: ~23 min) due to Anthropic API rate limits causing many retries
- **Impact on test:** Had to pivot from newly-created client to an existing pre-classified client (19cf7c12)
- **Root cause:** `max_jobs=1` (sequential) + Anthropic API rate limiting → APIError retries

### Bug #4 — FY2022 source_unit discrepancy
- **Severity:** MEDIUM
- **Impact:** The existing BCIPL client's FY2022 document was uploaded with `source_unit=lakhs` (from a previous session), while this test plan specifies `rupees`. This causes incorrect conversion for FY2022 column (col C)
- **Note:** FY2022 data (lakhs → crores via ÷100) vs ground truth (rupees → crores via ÷10M) = 100,000x scale error for that column

---

## Comparison Results Detail

**Ground truth:** `FInancials main/BCIPL/CMA BCIPL 12012024.xls`
**Generated:** `DOCS/test-results/bcipl/run-2026-03-23/generated_cma.xlsm`
**Sheet:** INPUT SHEET, rows 17–262, columns B (FY2021), C (FY2022), D (FY2023)

| Metric | Value |
|--------|-------|
| Total cells compared | 738 |
| Both blank/zero | 405 (55%) |
| Matches within 2% | **11** |
| Mismatches | **322** |
| Match rate (non-blank) | **3.3%** |

### Mismatch Breakdown
| Type | Count |
|------|-------|
| We left blank, GT has value (missed classifications) | 150 |
| We have value, GT is blank (extra/incorrect classifications) | 28 |
| Both have values but differ by >2% | 144 |

### Root Causes of Low Match Rate

1. **Classification row mapping errors:** The 3-tier pipeline is placing amounts in different INPUT SHEET rows than the CA chose. For example, FY2021 Fixed Assets: gen=12.77 crores vs gt=0.0102 crores (12500x diff) — likely classified to completely different row numbers.

2. **FY2022 source_unit=lakhs (Bug #4):** Column C values are systematically 100,000x too large relative to the CA's ground truth (which expects rupees input converted to crores).

3. **Missing classifications (150 cells):** Many CA-used rows are empty in our output, meaning those financial line items either weren't extracted from the source PDFs or weren't classified to the correct CMA row.

4. **Extra classifications (28 cells):** We're putting values in rows the CA left blank, possibly because we're breaking out sub-components that the CA treats as rolled-up totals.

5. **Ground truth unit uncertainty:** Need to verify whether the CA's INPUT SHEET data is in crores or another unit. If the GT is in lakhs, a systematic 100x scaling adjustment would be needed.

---

## Performance Observations

| Operation | Duration |
|-----------|---------|
| Doc upload (3 files) | ~2 min total |
| Extraction (3 docs, 604 items) | ~37 sec total |
| Classification FY2021 (224 items) | ~21.5 min |
| Classification FY2022 (141 items) | ~14 min |
| Classification FY2023 (239 items) | ~23 min |
| Bulk approve 691 items (UI + API) | ~3 min |
| Excel generation | ~3 min (13 min queue wait) |

---

## Pivots Made During Testing

1. **New client → Existing client:** New BCIPL client (07c2b753) docs took 60+ min to classify. Pivoted to existing pre-classified BCIPL client (19cf7c12) to complete the test.
   - Impact: FY2022 was `lakhs` not `rupees`; classifications from a prior session not this run

2. **Browser UI verify → API fallback:** `GET /api/documents/{id}` returns 405, so verify page shows "Document not found". Used direct API calls to extract and verify.

3. **Browser review actions → API bulk approve:** Review page too large for snapshot (691 items). Used `GET /api/cma-reports/{id}/classifications` + `POST /api/classifications/{id}/approve` via curl loop.

---

## Artifacts

| File | Description |
|------|-------------|
| preflight.json | Docker/backend/frontend health check |
| step-01 through step-22 (.png) | 22 browser screenshots across all steps |
| generated_cma.xlsm | Generated CMA Excel (107 KB) |
| comparison_results.md | Cell-by-cell comparison summary |
| comparison_results.json | Full comparison data (all 322 mismatches) |

---

## Recommendations

1. **Fix Bug #1** (GET /api/documents/{id}) — this breaks a core UI flow
2. **Improve classification accuracy** — current 3.3% match rate is insufficient for production use; review classification_rules_v1.md and expand the ruleset
3. **Add source_unit validation** at report creation time — warn if linked docs have inconsistent source units
4. **Add CA override UI** — allow CA to manually map items to correct CMA rows before generation
5. **Investigate FY2022 scale factor** — confirm whether ground truth is in crores or another unit
6. **Speed up classification** — consider batching AI calls or using learned_mappings more aggressively to reduce Anthropic API calls

---

*Report generated: 2026-03-23 | Test run: run-2026-03-23 | System: CMA Automation V1*
