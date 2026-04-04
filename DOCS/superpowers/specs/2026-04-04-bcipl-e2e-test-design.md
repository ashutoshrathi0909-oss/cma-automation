# BCIPL E2E Test + Excel Verification — Design Spec

**Date:** 2026-04-04
**Company:** BCIPL (Bagadia Chaitra Industries Pvt Ltd) — Manufacturing
**Goal:** Full app verification + generated CMA Excel accuracy test

---

## Overview

Two Claude Code windows run sequentially:

1. **Window 1 — E2E App Test**: Playwright browser walkthrough of the entire CMA workflow. Opus resolves classification doubts using CA domain knowledge. Fix-if-broken loop with /autoresearch:debug fallback.
2. **Window 2 — Excel Comparison**: Cell-by-cell comparison of the generated CMA Excel against the human-prepared ground truth. Includes formula breakdown analysis showing which line items contribute to each cell.

---

## Test Data

| Field | Value |
|-------|-------|
| Company | BCIPL |
| Industry | Manufacturing (Metal Stamping / Laminations) |
| Financial Years | FY2021, FY2022, FY2023 |
| Source files location | `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/` |
| Source file 1 (FY2021) | `6. BCIPL_ Final Accounts_2020-21.xls` — **rupees** |
| Source file 2 (FY2022) | `6. BCIPL_ Final Accounts_2021-22.xls` — **lakhs** |
| Source file 3 (FY2023) | `BCIPL_ FY 2023 Final Accounts_25092023.xls` — **rupees** |
| Ground truth CMA | `CMA BCIPL 12012024.xls` (same directory) |
| Ground truth unit | **Crores** (B13 = `'In crs'`) |
| CMA output unit | **crores** |
| Auth credentials | `ashutosh@cma-test.in` / `CmaTest@2026` (admin) |
| User ID | `b6352de6-5526-4c3c-9344-72bfd5765b87` |

### Unit Conversion Math
- FY2021 (rupees → crores): divide by 10,000,000
- FY2022 (lakhs → crores): divide by 100
- FY2023 (rupees → crores): divide by 10,000,000

---

## Infrastructure

| Service | URL | Status |
|---------|-----|--------|
| Backend (FastAPI) | http://localhost:8000 | Running |
| Frontend (Next.js) | http://localhost:3002 | Running |
| Worker (ARQ) | — | Running |
| Redis | localhost:6379 | Running |
| Supabase | sjdzmkqfsehfpptxoxca (ap-southeast-2) | ACTIVE_HEALTHY |
| Auth | Real Supabase Auth (DISABLE_AUTH=false) | Active |

---

## Window 1: E2E App Test

### API Reference (exact paths)

```
Auth:        POST /api/auth/login
Clients:     POST /api/clients/
             GET  /api/clients/
Documents:   POST /api/documents/           (multipart upload)
             GET  /api/documents/?client_id=X
             GET  /api/documents/{id}
Extraction:  GET  /api/documents/{id}/sheets
             POST /api/documents/{id}/extract
             GET  /api/documents/{id}/items
             PATCH /api/documents/{id}/items/{item_id}
             POST /api/documents/{id}/verify
Classify:    POST /api/documents/{id}/classify
             GET  /api/documents/{id}/classifications
             GET  /api/documents/{id}/doubts
             POST /api/classifications/{id}/approve
             POST /api/classifications/{id}/correct
             POST /api/documents/{id}/bulk-approve
CMA Reports: POST /api/clients/{cid}/cma-reports
             GET  /api/cma-reports/{rid}
             GET  /api/cma-reports/{rid}/confidence
             GET  /api/cma-reports/{rid}/classifications
             POST /api/cma-reports/{rid}/generate
             GET  /api/cma-reports/{rid}/download
```

### Frontend URLs

```
Login:       http://localhost:3002/login
Clients:     http://localhost:3002/clients
New Client:  http://localhost:3002/clients/new
Client:      http://localhost:3002/clients/{cid}
Upload:      http://localhost:3002/clients/{cid}/upload
Verify:      http://localhost:3002/cma/{did}/verify
Report:      http://localhost:3002/cma/{rid}
Review:      http://localhost:3002/cma/{rid}/review
Doubts:      http://localhost:3002/cma/{rid}/doubts
Generate:    http://localhost:3002/cma/{rid}/generate
```

### 13-Step Walkthrough

| Step | Feature | Action | Pass Condition |
|------|---------|--------|----------------|
| 1 | Login | Email + password via Supabase Auth | Redirect to /clients |
| 2 | Create Client | Name: BCIPL, Industry: Manufacturing | Client in list, client_id saved |
| 3 | Upload FY2021 | .xls, combined_financial_statement, 2021, audited, rupees | Success toast |
| 4 | Upload FY2022 | .xls, combined_financial_statement, 2022, audited, **lakhs** | Success toast |
| 5 | Upload FY2023 | .xls, combined_financial_statement, 2023, audited, rupees | Success toast |
| 6 | Extract all 3 | Trigger extraction, wait for completion | 30-200 items each |
| 7 | Verify all 3 | Review items, confirm extraction | Status = verified |
| 8 | Create Report | Title: "BCIPL CMA", output_unit: crores, select all 3 docs | Report page loads |
| 9 | Classify | Trigger classification, wait | All items classified |
| 10 | Resolve Doubts | Opus reads each doubt, applies CA knowledge, picks CMA field | Each doubt resolved with reasoning |
| 11 | Generate Excel | Trigger generation, wait | Status = complete |
| 12 | Download | Save .xlsm via Playwright | File > 50KB at known path |
| 13 | Logout | Click logout | Redirect to /login |

### Step 10: Doubt Resolution Protocol

For each doubt item, Opus:
1. Reads the `source_text` (line item description from the financial statement)
2. Reads the `amount` and `section` (P&L or BS)
3. Reads the `doubt_reason` and `ai_best_guess`
4. Reads the `alternative_fields` (up to 3 options)
5. Uses CA domain knowledge to decide the correct CMA field:
   - Manufacturing items → manufacturing expense rows (41-56)
   - Admin/office items → admin expense rows (67-77)
   - Selling items → selling expense rows (70-71)
   - Finance items → finance rows (83-85)
   - Tax items → tax rows (99-101)
   - BS current assets → asset rows (193-238)
   - BS current liabilities → liability rows (242-258)
6. Calls the correct API endpoint to resolve:
   - If AI guess was correct: POST /api/classifications/{id}/approve
   - If AI guess was wrong: POST /api/classifications/{id}/correct with the right CMA field
7. Documents the reasoning for each doubt

### Fix-If-Broken Workflow

```
Step fails
  → Screenshot the error
  → Read error logs (docker compose logs --tail=50 backend/worker)
  → Diagnose root cause
  → Fix the code (edit the file)
  → Rebuild: docker compose up -d --build backend worker
  → Wait 15s for services to restart
  → Retry the failed step
  → STILL broken?
      → Apply /autoresearch:debug (scientific method loop)
      → Max 3 autoresearch iterations
      → If still broken after 3: document the bug, skip step, continue
```

### Cost Tracking
- Record OpenRouter balance BEFORE test: `curl https://openrouter.ai/api/v1/auth/key` (with API key)
- After test completes, check balance again
- Count worker API calls from logs: `docker compose logs worker | grep "OpenRouter" | wc -l`

### Output Artifacts
All saved to `DOCS/test-results/bcipl/run-2026-04-04/`:
- Screenshots at every step (`step-01-login.png` through `step-13-logout.png`)
- Playwright video recording (`.webm`)
- `doubt-resolutions.json` — Opus's reasoning for each doubt
- `BCIPL_generated_CMA.xlsm` — the downloaded Excel
- `test-report-e2e.md` — full test report

---

## Window 2: Excel Comparison

### Inputs
- Generated: `DOCS/test-results/bcipl/run-2026-04-04/BCIPL_generated_CMA.xlsm` (from Window 1)
- Ground truth: `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/CMA BCIPL 12012024.xls`

### Three Levels of Comparison

#### Level 1: Structure Verification
| Check | Expected |
|-------|----------|
| File format | .xlsm (macros preserved) |
| Sheets present | INPUT SHEET, TL, Details, Summary spread, Cash flows, etc. |
| Row 7 (Client name) | "BCIPL" |
| Row 8 (Years) | B:2021, C:2022, D:2023, E:2024 |
| Row 10 (Nature) | B:Audited, C:Audited, D:Audited |
| Row 13 (Units) | "In crs" |
| Projection columns (E-H) | Formulas preserved, not overwritten |

#### Level 2: Data-Entry Cell Comparison
Only compare cells that the app writes (from `cma_field_rows.py`):
- 59 P&L fields (rows 22-108)
- 81 BS fields (rows 116-258)
- Columns B, C, D (FY2021, FY2022, FY2023)
- Tolerance: 2% (for rounding)

For each cell:
- **MATCH**: within 2% of ground truth
- **MISMATCH**: differs by >2% — show expected, got, diff%
- **MISSING**: ground truth has value, generated is empty/0
- **EXTRA**: generated has value, ground truth is empty (info only)

#### Level 3: Formula Breakdown Analysis
For each cell where the generated Excel has a formula (e.g., `=50000+30000-5000`):
- Parse the formula into individual components
- Show: `Row 22 (Domestic Sales) = 96.58 ← =X+Y (line items A + B)`
- For MISMATCHED cells: identify which component is wrong or missing
- For MISSING cells: check if the line item was extracted but classified to a different row

### Classification Trace-Back
For every MISMATCH or MISSING cell:
1. Look up what CMA field maps to that row (from `cma_field_rows.py`)
2. Query the classifications data to find items classified to that row
3. If items are missing → check if they were classified to a DIFFERENT row (misroute)
4. If amounts are wrong → check unit conversion (was the divisor correct for that document?)
5. If doubt-resolved → note that Opus made a classification decision here

### Error Taxonomy
| Code | Type | Description |
|------|------|-------------|
| A | Synonym Miss | Same concept, different wording |
| B | Industry Context | Industry changes the mapping |
| C | Conditional | Amount/context determines field |
| D | Aggregation | Sub-items need netting |
| E | Correct Doubt | AI rightly flagged uncertainty |
| F | Unit Error | Wrong conversion, double-conversion |
| G | Extraction Error | Wrong amount from source document |
| H | Misroute | Classified to wrong CMA row |
| I | Missing Item | Line item not extracted at all |

### Output: Comparison Report
Saved to `DOCS/test-results/bcipl/run-2026-04-04/comparison-report.md`:

```
# BCIPL CMA Comparison Report — 2026-04-04

## Summary
| Metric | Count |
|--------|-------|
| Data-entry cells in ground truth | XX |
| Matching (within 2%) | XX |
| Mismatched | XX |
| Missing | XX |
| Extra (generated only) | XX |
| **Data-entry accuracy** | **XX.X%** |

## Mismatched Cells (with breakdown)
| Row | CMA Field | FY | Expected | Got | Diff% | Breakdown | Error Type |
|-----|-----------|-----|----------|-----|-------|-----------|------------|

## Missing Cells (with trace)
| Row | CMA Field | FY | Expected | Possible Cause |
|-----|-----------|-----|----------|----------------|

## Formula Verification (multi-item cells)
| Row | CMA Field | FY | Formula | Components | Correct? |
|-----|-----------|-----|---------|------------|----------|

## Unit Conversion Verification
| Row | CMA Field | FY2021 (B) | FY2022 (C) | FY2023 (D) | Same Magnitude? |
|-----|-----------|------------|------------|------------|-----------------|
(For 10 key rows)

## All Matching Cells
| Row | CMA Field | FY | Expected | Got |
|-----|-----------|-----|----------|-----|
```

---

## Success Criteria

| Metric | Target | Gate |
|--------|--------|------|
| All 13 E2E steps complete | Yes (fixes allowed) | HARD |
| Login with real auth works | Yes | HARD |
| Extraction: 30-200 items per doc | All 3 | HARD |
| No AI failures ("unavailable") | 0 | HARD |
| Doubt resolution: documented reasoning | Each doubt | HARD |
| Excel generation completes | Yes | HARD |
| File format: .xlsm with macros | Yes | HARD |
| Unit conversion: same magnitude across FYs | Yes | HARD |
| Data-entry accuracy | >= 85% | SOFT |
| Full sheet accuracy | >= 70% | SOFT |
| Total API cost | < $1.00 | SOFT |
| Bugs found and documented | All | SOFT |

---

## Timing Estimate

| Phase | Est. Time |
|-------|-----------|
| Window 1: Steps 1-5 (auth + upload) | 10 min |
| Window 1: Steps 6-7 (extract + verify) | 10 min |
| Window 1: Steps 8-9 (report + classify) | 20-60 min |
| Window 1: Step 10 (doubt resolution) | 10 min |
| Window 1: Steps 11-13 (generate + download + logout) | 5 min |
| Window 2: Excel comparison | 15 min |
| **Total** | **70-110 min** |
| **Estimated API cost** | **$0.15-0.50** |
