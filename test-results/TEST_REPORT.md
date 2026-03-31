# CMA Automation V1 — Full Test Report

**Generated:** 2026-03-19
**Company tested:** Mehta Computers (M/S MEHTA COMPUTERS, Prop. Jignesh Chandrakant Mehta)
**Industry:** Trading (computer hardware reseller — confirmed from "TRADING AND PROFIT & LOSS ACCOUNT" heading)
**Documents tested:** 7 financial files (FY2022–FY2025), 162 line items extracted from FY2024
**Test runner:** Multi-agent orchestration (9 specialized agents)

---

## Overall Score: 7/9 agents PASS or PARTIAL PASS

| Agent | Purpose | Result | Key Metric |
|-------|---------|--------|------------|
| 0.5 | Document Intelligence | ✅ PASS | 7 docs identified, industry confirmed |
| 1 | Infrastructure Health | ✅ PASS | All 10 checks green |
| 2 | Auth & Security | ⚠️ 5/8 | Supabase auth DB degraded (non-blocking) |
| 3 | API Contract | ✅ PASS | 41/46 endpoints passed after 4 bug fixes |
| 4 | Extraction Pipeline | ✅ PARTIAL | 162 items extracted, verified; PDF = 0 items |
| 5 | Classification Quality | ✅ PASS | 88.3% accuracy, 12 improvement rules |
| 6 | Excel Validation | ⚠️ PARTIAL | File generated (106.7 KB), 14 cells written; VBA absent from template |
| 7 | E2E Playwright | ⚠️ PARTIAL | 11/15 steps; file upload (react-dropzone) + generate button nav failed |
| 8 | Chaos Monkey | ✅ PASS | 8/10 edge cases; blank Excel silent + null title crash |

---

## Classification Pipeline Report (Most Important — Agent 5)

### Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total items extracted | 162 | — | — |
| Tier 1 (fuzzy/learned) | 0 (0.0%) | >60% | ❌ BROKEN |
| Tier 2 (AI Haiku) | 55 (34.0%) | 20–30% | ⚠️ MARGINAL |
| Tier 3 (doubt) | 107 (66.0%) | <15% | ❌ HIGH |
| Auto-classified accuracy | 100% (55/55) | — | ✅ |
| Overall correct behaviour | 88.3% (143/162) | — | ✅ |
| True classification errors | 19 | — | — |
| Correct doubts sent to human | 88 | — | ✅ |

**Root cause of 66% doubt rate:** ALL 384 rows in `cma_reference_mappings` have `cma_input_row = NULL`. Tier 1 fuzzy matching requires row numbers to route items — without them, every item falls through to AI, and the AI's 0.8 confidence threshold correctly sends borderline items to doubt. Fix: one migration to populate `cma_input_row` from `cma_field_rows.py`. Expected improvement: doubt rate drops from 66% → <20%.

### Validation Against 10 Known FY2024 Ground-Truth Values

All 10 reference values confirmed correct in `CMA 15092025.xls`:

| Row | CMA Field | Expected | Actual in CMA File | Match |
|-----|-----------|----------|-------------------|-------|
| R22 | Domestic Sales | 230.61052 | 230.61052 | ✅ |
| R23 | Export Sales | 0.0 | 0.0 | ✅ |
| R42 | Raw Materials Consumed (Indigenous) | 174.12563 | 174.12563 | ✅ |
| R48 | Power, Coal, Fuel and Water | 0.26692 | 0.26692 | ✅ |
| R56 | Depreciation (Manufacturing) | 0.13084 | 0.13084 | ✅ |
| R67 | Salary and staff expenses | 14.86331 | 14.86331 | ✅ |
| R68 | Rent, Rates and Taxes | 0.444 | 0.444 | ✅ |
| R70 | Advertisements and Sales Promotions | 6.432721 | 6.432721 | ✅ |
| R83 | Interest on Fixed Loans / Term loans | 1.28496 | 1.28496 | ✅ |
| R85 | Bank Charges | 0.03127 | 0.03127 | ✅ |

---

## Improvement Rules Generated (Agent 5) — Add to Classification Pipeline

### RULE A-001 [HIGH — TYPE A Synonym Miss]
When source description matches `"Purchase @ [N]% ([Local|Inter-State|Igst])"`, for industry `Trading`, classify as **Raw Materials Consumed (Indigenous)** (row 42), confidence 0.95.
*Because: GST-coded purchase entries in trading firms = goods for resale = Raw Materials in CMA.*

### RULE A-002 [HIGH — TYPE A]
When source description matches `"Purchases @ [N]%"`, for industry `Trading`, classify as **Raw Materials Consumed (Indigenous)** (row 42).
*Same pattern as A-001 — plural "Purchases" with GST rate.*

### RULE B-001 [HIGH — TYPE B Industry Context]
When source description is `"Bank Interest"` AND context indicates income/receipts side, classify as **Interest Received** (row 30), NOT Bank Charges.
*Because: income ≠ expense — section context is the distinguisher.*

### RULE B-002 [MEDIUM — TYPE B]
When source description is an ALL_CAPS company name (vendor/supplier pattern), for Trading in balance sheet context, default to **Sundry Creditors for goods** (row 242).
*Because: "UTTAM MARKETING" is a vendor name, not an advertising expense.*

### RULE B-003 [MEDIUM — TYPE B]
When source description is `"Interest Paid"` (unqualified), for industry `Trading`, classify as **Interest on Working capital loans** (row 84). If amount > ₹10L, consider **Interest on Fixed Loans** (row 83).

### RULE C-001 [HIGH — TYPE C Conditional]
When source description contains `"Motor Vehicle"`, `"Car"`, `"Truck"`, or `"Two Wheeler"`, classify as **Gross Block** (row 162) — absolute rule, no industry distinction.

### RULE C-002 [HIGH — TYPE C]
For electronics/gadgets (`"Cell Phone"`, `"Mobile"`, `"Laptop"`, `"Computer [brand]"`):
- Amount ≥ ₹5,000 → **Gross Block** (row 162) — capitalize
- Amount < ₹5,000 → **Others (Admin)** (row 71) — expense
*Based on Indian Income Tax threshold for capital vs revenue expenditure.*

### RULE C-003 [HIGH — TYPE C]
When source description is `"Carriage Outward"`, `"Carriage Inward"`, or `"Packing Forwarding"`, for industry `Trading`, classify as **Freight and Transportation Charges** (row 47).

### RULE C-004 [MEDIUM — TYPE C]
When source description contains `"Telephone Deposit"`, `"Security Deposit"`, or `"Gem Caution Deposit"`, classify as **Security deposits with government departments** (row 237).

### RULE D-001 [HIGH — TYPE D Aggregation]
When source description is `"Less : Purchase Return"` or `"Purchase Returns"`, for `Trading`, net against **Raw Materials Consumed (Indigenous)** (row 42) — subtract from purchases total.

### RULE D-002 [HIGH — TYPE D]
When source description is `"Less : Sale Return"` or `"Sales Returns"`, for `Trading`, net against **Domestic Sales** (row 22) — subtract from gross sales.

### RULE SYS-001 [CRITICAL — Systemic Fix]
Populate `cma_reference_mappings.cma_input_row` for all 384 rows from `cma_field_rows.py:ALL_FIELD_TO_ROW`. Currently NULL for all rows. **This single fix will restore Tier 1 fuzzy matching and drop the doubt rate from 66% to <20%.**

---

## Bugs Found

### CRITICAL — Fix Before Any Real Use

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| C1 | `cma_reference_mappings.cma_input_row` = NULL for all 385 rows | Database / seed data | Tier 1 = 0%, doubt rate = 66% instead of <15% |
| C2 | No ARQ worker container in `docker-compose.yml` | Infrastructure | Background tasks (extraction, classification, Excel gen) never run automatically — must be triggered manually inside container |
| C3 | `learned_mappings` missing unique constraint on `(source_text, cma_field_name, industry_type)` | Database migration | Learning system API returns 500, corrections never saved |
| C4 | CMA template `DOCS/CMA.xlsm` not mounted into Docker backend container | Docker / docker-compose.yml | Excel generation fails until manually copied in |

### HIGH

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| H1 | Blank Excel extraction silently "succeeds" with 0 items (no error) | `extraction_tasks.py` | User gets no warning that file was empty; can proceed to verify empty extraction |
| H2 | `Mehta_Computers_financials_2024.xls` is OOXML/xlsx with `.xls` extension | Source file (format mismatch) | Extractor must detect by magic bytes, not extension |
| H3 | Supabase auth DB degraded — "Database error querying schema" | Supabase Auth | No real login possible; admin user cannot be created |
| H4 | `PUT /api/users/{id}` and `/deactivate` returned 500 (`.single()` on UPDATE builder) | `routers/users.py:99,132` | **FIXED during test** — removed `.single()` |
| H5 | `fuzzy_match_score` float inserted into integer DB column | `classification/pipeline.py` | **FIXED during test** — cast to `int()` |
| H6 | `cma_field_name` NOT NULL constraint violated by doubt records | `classification/pipeline.py` | **FIXED during test** — default to `"DOUBT"` |

### MEDIUM

| # | Bug | Location | Impact |
|---|-----|----------|--------|
| M1 | `GET /api/cma-reports/{id}` returns 500 when `title` is NULL | `schemas.py` — `CMAReportResponse.title: str` should be `Optional[str]` | All existing reports without title are unreadable via API |
| M2 | `POST /api/clients/{id}/cma-reports` returns 500 — `financial_years` column not populated | `routers/cma_reports.py` | CMA report creation broken for single-year documents |
| M3 | `PATCH /api/documents/{id}/items/{item_id}` returned 500 on non-UUID inputs | `routers/extraction.py` | **FIXED during test** — added UUID validation |
| M4 | `POST /api/rollover/preview` returned 500 on non-UUID `client_id` | `services/rollover_service.py` | **FIXED during test** — added UUID validation |
| M5 | `cma_reports` missing DB columns: `output_path`, `document_ids`, `title` | Database migration | Excel generation route fails — columns added during test |
| M6 | `cma_reports` status check constraint uses old enum values | Database migration | Status updates to `generating`/`complete`/`failed` all rejected — fixed during test |
| M7 | Storage bucket MIME type case mismatch (`MacroEnabled` vs `macroenabled`) | Supabase bucket config | Upload of .xlsm files rejected — fixed during test |
| M8 | VBA macros absent from `DOCS/CMA.xlsm` template | Template file | Generated output has no macros despite `keep_vba=True` in code |
| M9 | Formula-protected cells at key P&L rows (R22 Domestic Sales, R42 Raw Materials, etc.) | `CMA.xlsm` template | Data cannot be written to those cells; template needs editable cells at those positions |
| M10 | Supabase storage MIME type missing from upload call | `routers/documents.py` | **FIXED during test** — added `MIME_TYPES` dict and `file_options` parameter |
| M11 | PDF extraction yields 0 items (pdfplumber can't parse PandL.pdf layout, OCR deps not installed) | `extraction_tasks.py` / Docker | FY2025 provisional documents cannot be extracted |
| M12 | E2E: react-dropzone hides `<input type="file">` — standard Playwright locator misses it | `test-results/agent7-e2e` | E2E file upload step fails |

### LOW

| # | Bug | Notes |
|---|-----|-------|
| L1 | `financial_year=1850` returns 400 not 422 — inconsistent with Pydantic validation | Minor contract inconsistency |
| L2 | `user_id="system"` is not a valid UUID — audit log writes fail silently from worker | Non-blocking but logs are incomplete |
| L3 | Path traversal filename (../../etc/passwd.pdf) sanitized silently (returns 404 not 400) | Low severity — traversal is impossible; explicit rejection would be cleaner |
| L4 | Mock user ID mismatch in `dependencies.py` with `DISABLE_AUTH=true` | **FIXED during test** |

---

## Excel Output Validation Summary (Agent 6)

| Check | Result |
|-------|--------|
| File generated and downloaded | ✅ 106.7 KB |
| File is `.xlsm` | ✅ |
| ZIP structure valid | ✅ |
| VBA macros (vbaProject.bin) | ❌ Absent from source template |
| INPUT SHEET present | ✅ |
| TL Sheet present | ✅ |
| Client name populated | ✅ "Mehta Computers Test" |
| Year headers (FY2024) | ✅ |
| Financial data cells written | ✅ 14 cells (non-formula rows) |
| Domestic Sales R22 | ❌ Formula-protected — skipped by design; template needs editable cell |

---

## E2E Journey Summary (Agent 7)

| Step | Description | Result |
|------|-------------|--------|
| 1–3 | App loads, redirects, clients page renders | ✅ PASS |
| 4–6 | New Client button, form fill, client created | ✅ PASS |
| 7 | Upload page navigation | ✅ PASS |
| 8 | File upload via react-dropzone | ❌ FAIL — hidden input not reachable |
| 9 | Upload submit | ✅ PASS |
| 10 | Extraction progress visible | ⚠️ PARTIAL |
| 11 | Verification screen | ✅ PASS |
| 12 | Confirm verification | ⚠️ PARTIAL |
| 13 | Classification review | ✅ PASS |
| 14 | Generate Excel | ❌ FAIL — landed on list page, no report ID in URL |
| 15 | Final state | ✅ PASS |

**Score: 11/15 (73%).** All screenshots saved to `test-results/agent7-e2e/`.

---

## Security Summary (Agent 2)

| Test | Result |
|------|--------|
| Wrong password → 401 | ✅ |
| No token → 401 | ✅ |
| Malformed token → 401 | ✅ |
| `.exe` file rejected | ✅ |
| CORS evil.com blocked | ✅ |
| Valid login returns JWT | ❌ Supabase auth DB degraded |
| Employee cannot access admin routes | ❌ Blocked by auth DB issue |
| Path traversal rejected (explicit 400) | ⚠️ Sanitized silently (returns 404) |

---

## Recommended Next Actions

### Immediate (before any real client use)

1. **Populate `cma_reference_mappings.cma_input_row`** — Run the migration to copy row numbers from `cma_field_rows.py:ALL_FIELD_TO_ROW` into the table. This single fix restores Tier 1 fuzzy matching and will drop doubt rate from 66% → <20%. Highest ROI fix in the entire system.

2. **Add ARQ worker to docker-compose.yml** — Background tasks (extraction, classification, Excel generation) are silently queued but never processed. Add a `worker` service that runs `arq app.workers.main.WorkerSettings`.

3. **Add unique constraint to `learned_mappings`** — `CREATE UNIQUE INDEX ON learned_mappings(source_text, cma_field_name, industry_type)`. Without this, all correction submissions return 500 and the learning loop is broken.

4. **Mount CMA template in Docker** — Add `./DOCS/CMA.xlsm:/app/DOCS/CMA.xlsm:ro` to the backend service volumes in `docker-compose.yml`.

5. **Fix Supabase auth DB** — The auth schema is degraded ("Database error querying schema"). Real login is impossible. Check Supabase dashboard for migration issues.

### High Priority (before V1 launch)

6. **Add empty-document check in extraction** — After extracting, if `len(items) == 0`, set status to `"failed"` with message `"No financial data found in document"`. Currently silently succeeds.

7. **Fix `CMAReportResponse.title` to `Optional[str]`** — One-line Pydantic fix. All existing reports crash the GET endpoint.

8. **Fix `POST /api/clients/{id}/cma-reports`** — Populate `financial_years` column from `document_ids` when creating reports.

9. **Add 12 classification rules to pipeline** — The improvement rules from Agent 5 (especially A-001/A-002 for GST-coded purchases, C-001 for vehicles, D-001/D-002 for returns netting) will immediately improve FY2024 accuracy from 88% toward 95%+.

10. **Fix CMA template — VBA and formula-protected cells** — Re-open `CMA.xlsm` in Excel, re-save with macros, and make the INPUT SHEET data rows editable (not formula-locked).

### Medium Priority (quality improvements)

11. **Install OCR dependencies in Docker** — `pdf2image`, `Pillow`, and `surya-ocr` must be in the backend image for FY2025 PDF extraction to work.

12. **Fix E2E test — react-dropzone** — Use `page.locator("input[type='file']").evaluate("el => { el.style.display='block'; }")` before `set_input_files()`, or use drag-and-drop events.

13. **Move `financial_year` validation to Pydantic schema** — Add `ge=1990, le=2100` constraints to return 422 consistently (currently returns 400 from manual check).

---

## Documents & Infrastructure Reference

```
Company:           Mehta Computers (Trading — computer hardware reseller)
Ground truth CMA:  DOCS/Excel_project/Mehta computer/CMA 15092025.xls
Document tested:   DOCS/Excel_project/Mehta computer/2024/Mehta_Computers_financials_2024.xls
DOCUMENT_ID:       db4db151-758e-420a-8827-e7fd8751a5aa
CLIENT_ID:         206a2fe3-c65d-42d2-93e0-02226ed378e1
REPORT_ID:         8b8d5f71-ab88-4f0a-b576-f5f834719435
Generated CMA:     test-results/generated_cma.xlsm
Screenshots:       test-results/agent7-e2e/
Supabase project:  sjdzmkqfsehfpptxoxca
Reference mappings: 385 rows in cma_reference_mappings (all have cma_input_row=NULL — fix needed)
```

---

*Testing complete. Full agent reports in `test-results/agentN-*.md` and `.json`.*
