# CMA Automation System — Complete Testing & Development Log

**Last updated:** 2026-03-22
**Author:** Compiled from all Claude Code sessions (March 15–22, 2026)

---

## Table of Contents

1. [Project Timeline](#1-project-timeline)
2. [Test Session 1: Mehta Computers (March 19)](#2-test-session-1-mehta-computers)
3. [Test Session 2: Dynamic Air Engineering (March 19)](#3-test-session-2-dynamic-air-engineering)
4. [Test Session 3: MSL — Matrix Stampi Ltd (March 22)](#4-test-session-3-msl)
5. [Test Session 4: 7-Company Classification Analysis (March 22)](#5-test-session-4-7-company-analysis)
6. [Test Session 5: BCIPL Bug Fixes & Prep (March 22)](#6-test-session-5-bcipl-bug-fixes)
7. [Test Session 6: BCIPL End-to-End (In Progress)](#7-test-session-6-bcipl-e2e)
8. [Master Bug Registry](#8-master-bug-registry)
9. [AI Model History](#9-ai-model-history)
10. [Cost Tracking](#10-cost-tracking)
11. [Current System State](#11-current-system-state)

---

## 1. Project Timeline

| Date | Phase | What Happened |
|------|-------|---------------|
| Mar 15 | Build Phase 0-5 | Scaffold, DB, Auth, Clients, Upload, Extraction, Classification — all built in one day |
| Mar 16 | Build Phase 6-9 | Review UI, Excel Generator, Advanced Features, Production Polish — V1 "complete" |
| Mar 16 | V1 Merge | `623556d feat: merge phase-9-production-ready into master — V1 complete` |
| Mar 19 | Test Session 1 | Mehta Computers — 9-agent test suite, first real company test |
| Mar 19 | Test Session 2 | Dynamic Air Engineering — multi-agent test, first scanned PDF test |
| Mar 19 | Frontend Design | Stitch designs created (orange/blue/white theme), approved, deferred to after testing |
| Mar 22 | Test Session 3 | MSL (Matrix Stampi Ltd) — manufacturing company, revealed critical Excel bugs |
| Mar 22 | Test Session 4 | 7-Company classification analysis — 119 rules created from 7 real companies |
| Mar 22 | Test Session 5 | BCIPL bug fixes — 5 critical bugs fixed, Haiku via OpenRouter configured |
| Mar 22 | Test Session 6 | BCIPL end-to-end test — currently running |

### Git History (37 commits)

```
f13f797 2026-03-15 Phase 0+1: scaffold, DB, auth
ae66034 2026-03-15 Phase 2: client management
ab77440 2026-03-15 Phase 4: extraction pipeline
570070c 2026-03-15 Phase 5: classification engine
37e14db 2026-03-16 Phase 6: review interface
acb1c13 2026-03-16 Phase 7: excel generator (27 tests, 100% coverage)
847b1eb 2026-03-16 Phase 7 merge
c754873 2026-03-16 Phase 8: advanced features
623556d 2026-03-16 Phase 9 merge — V1 complete
eedcf5c 2026-03-16 Dashboard + 404 + polish
2f5b3fd 2026-03-16 Dev-bypass + CORS + sidebar fixes
```

---

## 2. Test Session 1: Mehta Computers

**Date:** March 19, 2026
**Company:** M/S Mehta Computers (Prop. Jignesh Chandrakant Mehta)
**Industry:** Trading (computer hardware reseller)
**Documents:** 7 financial files (FY2022–FY2025), Excel format
**Test Method:** 9 specialized agents (multi-agent orchestration)
**Test Report:** `test-results/TEST_REPORT.md`

### Overall Score: 7/9 agents PASS or PARTIAL PASS

| Agent | Purpose | Result | Key Finding |
|-------|---------|--------|-------------|
| 0.5 | Document Intelligence | PASS | 7 docs identified, industry confirmed |
| 1 | Infrastructure Health | PASS | All 10 checks green |
| 2 | Auth & Security | 5/8 | Supabase auth DB degraded |
| 3 | API Contract | PASS | 41/46 endpoints passed after 4 fixes |
| 4 | Extraction Pipeline | PARTIAL | 162 items extracted; PDF = 0 items |
| 5 | Classification Quality | PASS | 88.3% accuracy |
| 6 | Excel Validation | PARTIAL | File generated (106.7 KB); 14 cells written |
| 7 | E2E Playwright | PARTIAL | 11/15 steps; file upload failed |
| 8 | Chaos Monkey | PASS | 8/10 edge cases |

### Classification Results

| Metric | Value | Status |
|--------|-------|--------|
| Total items | 162 | — |
| Tier 1 (fuzzy) | 0 (0%) | BROKEN |
| Tier 2 (AI Haiku) | 55 (34%) | Marginal |
| Tier 3 (doubt) | 107 (66%) | Too high |
| Auto-classified accuracy | 100% (55/55) | Excellent |
| True errors | 19 | — |

**Root Cause of 66% Doubt Rate:** All 384 rows in `cma_reference_mappings` had `cma_input_row = NULL`. Fuzzy matching needs row numbers to work. Without them, everything fell through to AI, and Haiku's 0.8 confidence threshold correctly flagged borderline items.

### Excel Generation Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| VBA macros absent | HIGH | Template `CMA.xlsm` didn't contain `vbaProject.bin` |
| Formula cells block writes | HIGH | 18 cells had `=0` formulas — generator correctly skips them |
| Missing DB columns | HIGH | `output_path`, `document_ids`, `title` missing from `cma_reports` |
| No ARQ worker | HIGH | No separate worker container in docker-compose.yml |
| learned_mappings constraint | MEDIUM | Missing unique constraint on `(source_text, cma_field_name, industry_type)` |
| MIME type case mismatch | LOW | Supabase bucket had mixed-case MIME vs Python lowercase |

### 12 Classification Rules Generated

Rules A-001 through D-002 created from Mehta analysis. Key ones:
- A-001: "Purchase @ N% (Local/Inter-State/IGST)" → Raw Materials (R42)
- B-001: "Bank Interest" in income context → Interest Received (R30)
- C-001: Motor Vehicle/Car/Truck → Gross Block (R162) — absolute rule
- C-002: Electronics ≥ ₹5K → capitalize (R162), <₹5K → expense (R71)
- D-001: "Purchase Returns" net against purchases (R42)

### Ground Truth Validation — 10/10 MATCH

All 10 reference values from the manually-prepared CMA matched perfectly:
- Domestic Sales: 230.61052 ✅
- Export Sales: 0.0 ✅
- Raw Materials: 174.12563 ✅
- Power/Fuel: 0.26692 ✅
- Depreciation: 0.13084 ✅
- Salary: 14.86331 ✅
- Rent: 0.444 ✅
- Advertisements: 6.432721 ✅
- Interest on Fixed Loans: 1.28496 ✅
- Bank Charges: 0.03127 ✅

---

## 3. Test Session 2: Dynamic Air Engineering

**Date:** March 19, 2026
**Company:** Dynamic Air Engineering India Pvt Ltd
**Industry:** Manufacturing (air handling equipment)
**Documents:** 5 PDFs (ALL scanned) + 2 Excel files (FY22-FY25)
**Test Method:** Multi-agent (specialized agents)
**Test Report:** `test-results/dynamic/`

### Key Finding: ALL PDFs Are Scanned

All 5 PDFs were scanned images, not just FY24. This meant ~80+ pages of Vision OCR (not 33). Total extraction time: 25-35 minutes.

### Extraction Results

| Document | Year | Items | Time |
|----------|------|-------|------|
| BS-Dynamic 2022 Excel | FY22 | 1887 | 5s |
| Notes to Financials.pdf | FY22 | 195 | 155s |
| ITR BS P&L.pdf | FY22 | 166 | 144s |
| ITR PL & BS.pdf | FY23 | 109 | 103s |
| Notes..pdf | FY23 | 185 | 143s |
| Audited Financials FY24 | FY24 | 290 | 267s |
| Provisional FY25 Excel | FY25 | 139 | 20s |
| **Total** | | **2971** | |

### CMA Ground Truth (in Lakhs)

Cross-validated against `CMA Dynamic 23082025.xls`. All values matched:
- Domestic Sales FY22: 46.079, FY23: 69.437, FY24: 67.150, FY25: 77.579
- Net Profit FY25: 0.966 (₹96,60,162 in rupees → 0.966 in lakhs ✅)

### Bugs Fixed During This Session

1. Mock user ID mismatch → fixed FK constraint
2. Storage MIME type → added content-type header
3. DB column mismatch → `description` vs `source_text`
4. Supabase 1000-row limit → added pagination
5. pdf2image missing from Docker → installed
6. MAX_PAGES_PER_BATCH=15 → reduced to 5 (token overflow)
7. CMA report `financial_years` NOT NULL → auto-derive from docs
8. Worker not restarting on code changes → manual restart

### 23 Ambiguity Questions Found

Items where the extractor identified human judgment needed (e.g., "Wages vs Other Manufacturing split", "Employee benefits not broken down", "Raw Materials + Direct Costs combined").

---

## 4. Test Session 3: MSL

**Date:** March 22, 2026
**Company:** Matrix Stampi Ltd (MSL) — Metal Stamping / Dies, Kolkata
**Industry:** Manufacturing
**Document:** MSL - B.S -2024-25 Final 151025.xlsx (15 sheets)
**Source Units:** Rs. '000 (thousands) — CMA expects Lakhs
**Test Report:** `test-results/MSL_test_results.md`

### This Was the Most Revealing Test — Exposed Critical Excel Bugs

#### Extraction Results

| Metric | Value |
|--------|-------|
| Total items extracted | 752 |
| Key items found | 39 / 45 |
| Wrong amounts | 12 (ledger sheets in full Rs, not Rs.'000) |

**Key Finding:** Multi-sheet Excel mixing summary (Rs.'000) with ledger (full Rs.) creates unit inconsistency. App needs sheet-level filtering.

#### Classification Results

| Tier | Count | Status |
|------|-------|--------|
| Tier 0 (Rules) | 0 | FAIL — patterns don't match MSL's text |
| Tier 1 (Fuzzy) | 79 | PASS |
| Tier 2 (AI) | 0 | FAIL — Anthropic API key invalid/exhausted |
| Tier 3 (Doubt) | 673 (89%) | Cascading from AI failure |

**27 wrong auto-classifications** found. Major mismatches:
- Export Sales → R22 (should be R23)
- Bonus → R71 (should be R45)
- Bank Charges → R83 (should be R85)
- Advance Income Tax → R99 (should be R221)

#### Excel Generation — CATASTROPHIC: 1/52 Cells Correct (2%)

| Bug | Severity | Description |
|-----|----------|-------------|
| Formula cells block P&L writes | CRITICAL | 20+ P&L rows contain `=0` formulas → generator skips them all |
| **Field name mismatch** | **CRITICAL** | Pipeline produces `"Item 1 (i) : Domestic sales"` but `ALL_FIELD_TO_ROW` expects `"Domestic Sales"` → **35 of 98 classifications silently skipped** |
| Unit conversion missing | MAJOR | Rs.'000 values written directly without ÷100 to Lakhs |
| Year-column mismatch | MAJOR | Ground truth has FY2025 in Col E, app writes to Col D |
| API doubt guard too strict | MINOR | `/generate` blocks if ANY doubt remains |

**This test proved the Excel generator was fundamentally broken.** The field name lookup was the root cause — it could only match ~80 "canonical" names from `ALL_FIELD_TO_ROW`, but the classification pipeline produced 384+ different names from reference mappings.

---

## 5. Test Session 4: 7-Company Analysis

**Date:** March 22, 2026
**Method:** Manual analysis using Claude Code vision (no API costs)
**Report:** `DOCS/session-2026-03-22-files-created.md`

### 7 Companies Analyzed

| Company | Industry | Entity | Rules Created | Source |
|---------|----------|--------|---------------|--------|
| BCIPL | Manufacturing (stamping) | Pvt Ltd | 22 | Excel only |
| SR Papers | Distribution (paper) | Pvt Ltd | 22 | Excel only |
| SSSS | Trading (steel) | Pvt Ltd | 14 | Excel only |
| MSL | Manufacturing (metal) | Pvt Ltd | 10 | PDF + Excel |
| SLIPL | Manufacturing (shoes) | Pvt Ltd | 12 | PDF + Excel |
| INPL | Mfg + R&D hybrid | Pvt Ltd | 14 | PDF only (scanned) |
| Kurunji Retail | Retail trading | Partnership | 15 | PDF only (ITR) |

**Total: 119 rules created, ~85-90 unique after deduplication**

### 8 Unresolved Conflicts (Pending CA Verification)

| # | Conflict | Company A | Company B | Company C |
|---|----------|-----------|-----------|-----------|
| 1 | Directors Remuneration | BCIPL → R67 | SLIPL/MSL → R45 | INPL/Kurunji → R73 |
| 2 | Packing Materials | BCIPL → R70 | SLIPL → R49 | Kurunji → R44 |
| 3 | Related Party Loans | BCIPL/SSSS → R152 | INPL → R137 | — |
| 4 | Discount Received | SR Papers → R34 | SSSS → R42 | — |
| 5 | Retail Store Rent | Kurunji → R49 | All others → R68 | — |
| 6 | Generator Expenses | Kurunji → R71 | Standard → R48 | — |
| 7 | Export Incentives | MSL → Exclude | SLIPL → R23 | BCIPL → R34 |
| 8 | R&M in Manufacturing | MSL/INPL/BCIPL → R50 | SLIPL → R72 | — |

### Already Resolved (Confirmed by 2+ Companies)

| Pattern | CMA Row | Confirmed By |
|---------|---------|-------------|
| Motor Vehicles → Gross Block | R162 | All 7 companies |
| Job Work Charges → Processing | R46 | BCIPL + SSSS + SLIPL + MSL |
| Interest on Unsecured/Partner Loans | R83 | BCIPL + SSSS + INPL + Kurunji |
| Promoter/Director Loans → Quasi Equity | R152 | BCIPL + SSSS + SLIPL + MSL |
| Security Deposits: Govt → R237, Private → R238 | Split | SLIPL + INPL + Kurunji |

### Files Created

- 7 extraction reference files in `DOCS/extractions/`
- 7 classification rule files in `DOCS/rules/`
- Session report: `DOCS/session-2026-03-22-files-created.md`

---

## 6. Test Session 5: BCIPL Bug Fixes

**Date:** March 22, 2026
**Goal:** Fix all known bugs before BCIPL end-to-end test
**Company:** BCIPL (manufacturing, stamping/sheet metal)
**Documents:** 3 Excel files (FY21, FY22, FY23)

### The 5 Bugs Fixed

#### BUG-1 (BLOCKER): PostgREST URL Length Limit

**Symptom:** `get_classifications()` and `get_doubts()` crashed when a document had 700+ line items. All 752 UUIDs were passed in a single `.in_()` query, exceeding the ~8192 char HTTP URL limit.

**Root Cause:** PostgREST uses GET requests with query params. UUID strings are 36 chars each. 752 × 36 = 27,072 chars → way over limit.

**Fix:** Batch `.in_()` queries in chunks of 100 IDs.

**Files Changed:**
- `backend/app/routers/classification.py` — `get_classifications()` and `get_doubts()`
- `backend/app/routers/cma_reports.py` — `get_report_classifications()`
- `backend/app/services/excel_generator.py` — `_fetch_classified_data()`

#### BUG-2 (BLOCKER): Subnotes Over-Extraction

**Symptom:** Excel extractor was including "Subnotes to Balance Sheet" sheets, which are metadata/notes not financial data.

**Root Cause:** `_SUMMARY_PATTERNS` had `notes` which matched "Subnotes to BS". But `_SKIP_PATTERNS` was checked first and didn't have `sub\s*notes`.

**Fix:** Added `sub\s*notes?\b` to `_SKIP_PATTERNS` in `excel_extractor.py`.

#### BUG-3 (HIGH): AI Classifier Completely Non-Functional

**Symptom:** All AI classification calls returned errors.

**History:**
1. Initially used Anthropic Claude Haiku directly → API credits ran out
2. Switched to Minimax M2.7 via OpenRouter → 0% success rate (returned malformed JSON in tool call arguments)
3. Final fix: Claude Haiku via OpenRouter (`CLASSIFIER_MODEL=anthropic/claude-haiku-4-5`)

**Fix:**
- `.env`: `CLASSIFIER_PROVIDER=openrouter`, `CLASSIFIER_MODEL=anthropic/claude-haiku-4-5`
- `ai_classifier.py`: Changed `tool_choice` from `"auto"` to forced: `{"type": "function", "function": {"name": "classify_line_item"}}`
- Added `_repair_json()` method for handling malformed LLM outputs

#### BUG-4 (HIGH): Excel Generator Silent Data Loss

**Two sub-bugs working together to drop most data:**

**BUG-4a: Fuzzy Match False Positives**

**Symptom:** `token_set_ratio("Share Capital", "Redeemable Preference Share Capital (Series I)")` = 100.0 because ALL tokens of the shorter string appear in the longer one.

**Fix:** Added length penalty in `fuzzy_matcher.py` — penalizes when the matched reference string is much longer than the source text.

**BUG-4b: Row Lookup Mismatch (THE BIG ONE)**

**Symptom:** The Excel generator used `ALL_FIELD_TO_ROW.get(field)` to find which row to write data to. This static mapping only has ~80 canonical CMA field names. But the classification pipeline stores `cma_field_name` values from reference_mappings (384 entries) which use longer names like `"Item 1 (i) : Domestic sales"`. The lookup returned `None` for all non-canonical names → **data silently skipped**.

**Root Cause:** The pipeline stores `cma_row` in every classification record (from all 3 tiers). But the Excel generator was ignoring it and doing its own lookup.

**Fix:**
- `excel_generator.py`: `_fetch_classified_data()` now selects `cma_row` from classifications
- `_fill_data_cells()` now prefers `cma_row` from classification, falls back to static mapping only if `cma_row` is 0/None

```python
# Before (broken):
row = ALL_FIELD_TO_ROW.get(field)  # Only ~80 entries

# After (fixed):
row = item.get("cma_row") or ALL_FIELD_TO_ROW.get(field)  # Uses pipeline's row
```

#### BUG-5 (MEDIUM): "(no description)" in Classification UI

**Symptom:** The doubt resolution screen and classification list showed "(no description)" for every item, making it impossible for users to review classifications.

**Root Cause:** `ClassificationResponse` has `line_item_description` and `line_item_amount` fields, but the API endpoints only queried the `classifications` table without joining `extracted_line_items`.

**Fix:** All three endpoints now use PostgREST join + flatten:
```python
.select("*, extracted_line_items(source_text, amount)")
```
Then flatten the nested result into the response model.

**Files Changed:**
- `backend/app/routers/classification.py` — `get_classifications()` and `get_doubts()`
- `backend/app/routers/cma_reports.py` — `get_report_classifications()` (fixed in prior session)

### Per-Document Unit Conversion (Also Fixed This Session)

**Problem:** BCIPL has mixed units: FY2021 and FY2023 are in full Rupees, FY2022 is in Lakhs. A single `unit_divisor` would either over-divide FY2022 or under-divide FY2021/FY2023.

**Fix:** `doc_divisors` dict maps each `document_id` to its own divisor. Each item's amount is converted using its document's divisor BEFORE accumulation.

```python
doc_units = {d["id"]: d.get("source_unit") or "rupees" for d in docs}
doc_divisors = {
    doc_id: compute_unit_divisor(src_unit, cma_output_unit)
    for doc_id, src_unit in doc_units.items()
}
```

### Testing Harness Created

`DOCS/testing-harness-bcipl.md` — 6-phase test prompt:
- Phase 0: Data reset (purge old classifications, reset documents to pending)
- Phase 1: Extraction (trigger for 3 Excel files)
- Phase 2: Verification (mark as verified)
- Phase 3: Classification (trigger Haiku via OpenRouter)
- Phase 4: CMA Report + Excel generation
- Phase 5: Cell-by-cell comparison with ground truth CMA

---

## 7. Test Session 6: BCIPL End-to-End (In Progress)

**Date:** March 22, 2026
**Status:** Running in separate Claude Code window
**Test Prompt:** `DOCS/testing-harness-bcipl.md`

### BCIPL Test Configuration

| Setting | Value |
|---------|-------|
| Documents | 3 × Excel (FY21, FY22, FY23) |
| FY21 unit | Rupees (÷100,000 for Lakhs) |
| FY22 unit | Lakhs (÷1, no conversion) |
| FY23 unit | Rupees (÷100,000 for Lakhs) |
| Classifier | Claude Haiku via OpenRouter |
| Extractor | openpyxl (Excel files, no OCR needed) |
| Output unit | Lakhs |

### Expected Results

With all 5 bugs fixed:
- Extraction should find ~200-300 line items per year across 3 files
- Classification should use Haiku successfully (not the broken Minimax)
- Excel generator should use `cma_row` directly (not the broken field name lookup)
- Per-document unit conversion should handle the mixed Rupees/Lakhs correctly
- Generated CMA should match the ground truth CMA closely

**Awaiting results.**

---

## 8. Master Bug Registry

### All Bugs Found Across All Sessions

| # | Bug | Severity | Session | Status | Files Changed |
|---|-----|----------|---------|--------|---------------|
| 1 | `cma_reference_mappings` all have `cma_input_row = NULL` | CRITICAL | Mehta | Fixed (migration) | DB migration |
| 2 | No ARQ worker container in docker-compose | CRITICAL | Mehta | Fixed | docker-compose.yml |
| 3 | VBA macros absent from template | HIGH | Mehta | Fixed (re-saved template) | DOCS/CMA.xlsm |
| 4 | Formula cells `=0` block data writes in P&L rows | HIGH | Mehta + MSL | Fixed (template cleared) | DOCS/CMA.xlsm |
| 5 | Missing DB columns: output_path, document_ids, title | HIGH | Mehta | Fixed (migration) | DB migration |
| 6 | `cma_reports` status check constraint outdated | HIGH | Mehta | Fixed (migration) | DB migration |
| 7 | learned_mappings missing unique constraint | MEDIUM | Mehta | Fixed (migration) | DB migration |
| 8 | Mock user ID FK mismatch | MEDIUM | Dynamic Air | Fixed | extraction_tasks.py |
| 9 | Storage MIME type missing content-type header | MEDIUM | Dynamic Air | Fixed | upload code |
| 10 | DB column `description` vs `source_text` mismatch | MEDIUM | Dynamic Air | Fixed | extraction code |
| 11 | Supabase 1000-row default limit | MEDIUM | Dynamic Air | Fixed (pagination) | get_line_items endpoint |
| 12 | pdf2image not in Docker image | MEDIUM | Dynamic Air | Fixed | Dockerfile |
| 13 | MAX_PAGES_PER_BATCH=15 token overflow | MEDIUM | Dynamic Air | Fixed → 5 | ocr_extractor.py |
| 14 | `financial_years` NOT NULL on CMA reports | LOW | Dynamic Air | Fixed (auto-derive) | cma_reports.py |
| 15 | PostgREST URL length limit with 700+ UUIDs | BLOCKER | MSL + BCIPL | Fixed (batch 100) | classification.py, cma_reports.py, excel_generator.py |
| 16 | Subnotes sheet over-extraction | BLOCKER | BCIPL | Fixed | excel_extractor.py |
| 17 | Field name mismatch (`ALL_FIELD_TO_ROW` vs pipeline output) | CRITICAL | MSL + BCIPL | Fixed (use `cma_row` directly) | excel_generator.py |
| 18 | Unit conversion missing (Rs.'000 → Lakhs) | MAJOR | MSL | Fixed (per-doc divisors) | excel_generator.py |
| 19 | Year-column off-by-one | MAJOR | MSL | Fixed | excel_generator.py |
| 20 | `token_set_ratio` false positives | HIGH | BCIPL | Fixed (length penalty) | fuzzy_matcher.py |
| 21 | Minimax M2.7 broken JSON output | HIGH | BCIPL | Fixed (switched to Haiku) | .env, ai_classifier.py |
| 22 | Anthropic API credits exhausted | HIGH | MSL + BCIPL | Fixed (OpenRouter) | .env |
| 23 | "(no description)" in classification UI | MEDIUM | BCIPL | Fixed (PostgREST join) | classification.py |
| 24 | API doubt guard too strict for `/generate` | MINOR | MSL | Known | — |
| 25 | `user_id="system"` invalid UUID in audit log | LOW | Mehta | Known | — |
| 26 | Tier 0 rule patterns not matching MSL text | LOW | MSL | Known (rules need tuning) | — |
| 27 | MIME type case mismatch (mixed vs lowercase) | LOW | Mehta | Fixed | Supabase bucket config |
| 28 | `fuzzy_match_score` stored as float, DB expects int | LOW | Mehta | Fixed | pipeline.py |

### Bug Fix Impact Summary

| Fix | Impact |
|-----|--------|
| `cma_row` direct usage | Estimated 80%+ of data cells now write correctly (was ~2%) |
| Per-document unit conversion | Mixed-unit documents (like BCIPL) now convert correctly |
| Batched queries | No more crashes on documents with 100+ line items |
| Haiku via OpenRouter | AI classification functional again |
| PostgREST join for descriptions | Users can now see what they're classifying |

---

## 9. AI Model History

| Date | Component | Model | Provider | Result |
|------|-----------|-------|----------|--------|
| Mar 15-16 | Classification | Claude Haiku | Anthropic (direct) | Worked well, 100% accuracy on auto-classified items |
| Mar 19 | Classification | Claude Haiku | Anthropic (direct) | Worked for Mehta test |
| Mar 19 | OCR (scanned PDF) | Qwen3.5-9B | OpenRouter | Worked for Dynamic Air |
| Mar 22 | Classification | Claude Haiku | Anthropic (direct) | FAILED — API credits exhausted |
| Mar 22 | Classification | Minimax M2.7 | OpenRouter | FAILED — 0% success, malformed JSON |
| Mar 22 | Classification | Claude Haiku | OpenRouter | Current — working with forced tool_choice |
| Mar 22 | OCR | Qwen3.5-9B | OpenRouter | Current — working |

### Current `.env` Configuration

```
OCR_PROVIDER=openrouter
OCR_MODEL=qwen/qwen3.5-9b
CLASSIFIER_PROVIDER=openrouter
CLASSIFIER_MODEL=anthropic/claude-haiku-4-5
```

---

## 10. Cost Tracking

| Session | Provider | Estimated Cost | What For |
|---------|----------|---------------|----------|
| Mehta (Mar 19) | Anthropic | ~$0.30 | 162 Haiku classification calls |
| Dynamic Air (Mar 19) | OpenRouter | ~$1.50 | ~80 pages Vision OCR + classification |
| MSL (Mar 22) | Anthropic | $0.00 | API key exhausted, 0 successful calls |
| BCIPL (Mar 22) | OpenRouter | ~$0.10-0.30 (est.) | ~100-200 Haiku calls via OpenRouter |
| 7-Company Analysis | Claude Code | $0.00 (OpenRouter) | All analysis done via Claude Code vision |
| Runaway loop incident | OpenRouter | $3.00 (lost) | Unbounded API call loop during testing |

**Total estimated API spend:** ~$5.10

---

## 11. Current System State

### What Works

| Component | Status | Notes |
|-----------|--------|-------|
| Document upload (Excel) | WORKING | openpyxl extraction reliable |
| Document upload (PDF native) | WORKING | pdfplumber extraction |
| Document upload (PDF scanned) | WORKING | Qwen3.5 Vision OCR via OpenRouter |
| Excel sheet filtering | WORKING | Summary/P&L/BS sheets selected, subnotes/ledger skipped |
| Fuzzy classification (Tier 1) | WORKING | With length penalty fix |
| AI classification (Tier 2) | WORKING | Haiku via OpenRouter with forced tool_choice |
| Doubt report (Tier 3) | WORKING | Confidence < 0.8 always flagged |
| Classification UI | WORKING | Descriptions now show (PostgREST join fix) |
| Excel generation | FIXED (untested) | cma_row direct, per-doc units, batched queries |
| Unit conversion | FIXED (untested) | Per-document divisors |
| Docker services | RUNNING | backend + frontend + redis + worker |

### What's Not Tested Yet

| Component | Status | Notes |
|-----------|--------|-------|
| BCIPL end-to-end flow | IN PROGRESS | Running in another window |
| Generated CMA accuracy | UNKNOWN | Waiting for BCIPL test results |
| Rule Engine (Tier 0) | NOT IMPLEMENTED | 119 rules created but not coded |
| TL Sheet filling | NOT IMPLEMENTED | V1 scope but not coded yet |
| Frontend redesign | DEFERRED | Stitch designs approved, waiting for backend testing |
| Multi-year CMA with mixed units | BEING TESTED | BCIPL has mixed Rupees/Lakhs |

### Files Modified But Not Committed

All bug fixes from sessions 3-5 are uncommitted:
- `backend/app/services/excel_generator.py` — cma_row direct, per-doc units, batched queries
- `backend/app/routers/classification.py` — PostgREST join + batch
- `backend/app/routers/cma_reports.py` — PostgREST join + batch
- `backend/app/services/classification/ai_classifier.py` — forced tool_choice, JSON repair
- `backend/app/services/classification/fuzzy_matcher.py` — length penalty
- `backend/app/services/extraction/excel_extractor.py` — subnotes skip
- `.env` — OpenRouter Haiku config
- `docker-compose.yml` — worker container
- Plus: testing harnesses, extraction references, classification rules

### What Comes Next

1. **Immediate:** Wait for BCIPL test results, analyze CMA accuracy
2. **If CMA is accurate:** Commit all fixes, test 2-3 more companies
3. **If CMA has issues:** Fix identified problems, re-test
4. **After testing:** Get CA verification on 8 conflict items, implement 119 rules in rule_engine.py
5. **After rules:** Implement frontend redesign (orange/blue/white Stitch designs)
6. **After frontend:** Production deployment

---

*This document will be updated as more test results come in.*
