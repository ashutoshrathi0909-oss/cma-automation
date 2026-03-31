# SR Papers — Agent-Team App Verification

**Purpose:** Paste this into a fresh Claude Code session. It will deploy **3 focused agents** sequentially. No code changes needed — all fixes are already applied.

**Priority:** The #1 goal is verifying the generated CMA Excel has the correct numbers in the correct cells.

---

## COMPANY DETAILS

| Field | Value |
|-------|-------|
| Company | S.R.Papers Private Limited |
| Industry | Trading / Distribution (paper distributor, NOT manufacturer) |
| Source Files | 3 x `.xls` (Excel 97) in `FInancials main/SR Papers/` |
| Ground Truth CMA | `FInancials main/SR Papers/CMA S.R.Papers 09032026 v2.xls` |
| Source Unit | Full Rupees (`rupees`) |
| CMA Output Unit | Crores (`crores`) — divisor = 10,000,000 |
| Financial Years | FY2024 (col B), FY2025 (col C), FY2026 (col D) |
| Nature | All Audited |

**NOTE:** SR Papers is a **trading** company (buys and resells paper), NOT a manufacturer. This tests a different industry type than BCIPL (manufacturing).

---

## HOW THIS WORKS

You are the **orchestrator**. Deploy agents for each phase:

```
STEP 0: Pre-flight (YOU do this, no agent)
    - Verify Docker is running (should already be up from BCIPL test)
    - Verify DB migration was run
    ↓
AGENT 1: Upload + Extract + Verify
    ↓ passes client_id, document_ids
AGENT 2: Classify + Review doubts + Create report
    ↓ passes report_id
AGENT 3: Generate Excel + Compare vs ground truth
    ↓ saves file to DOCS/test-results/
```

**IMPORTANT orchestration rules:**
- Deploy agents ONE AT A TIME (each depends on the previous)
- **NEVER** create unbounded loops — max 20 polls, max 100 API calls per agent
- **NEVER** retry failed API calls more than 3 times

---

## STEP 0: Pre-flight (YOU do this)

Docker should already be running from the BCIPL test. Verify:
```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
curl http://localhost:8000/health
docker compose ps
```

If Docker is not running:
```bash
docker compose up -d
```

DB migration should already be done. If not, run in Supabase SQL Editor:
```sql
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS source_unit TEXT DEFAULT 'rupees'
  CHECK (source_unit IN ('rupees', 'thousands', 'lakhs', 'crores'));
ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS cma_output_unit TEXT DEFAULT 'lakhs'
  CHECK (cma_output_unit IN ('lakhs', 'crores'));
```

---

## SECTION A — AGENT 1 PROMPT: Upload + Extract + Verify

```
You are testing the CMA Automation System with SR Papers (a paper distribution company).

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000

DISABLE_AUTH is true — use any user_id for auth.

IMPORTANT LIMITS: Max 20 API polls, max 3 retries per call.

═══════════════════════════════════════════════════════════════
TASK 1: Create Client
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/
Body: { "name": "SR Papers", "industry_type": "trading" }

Save the client_id.

═══════════════════════════════════════════════════════════════
TASK 2: Upload 3 Documents
═══════════════════════════════════════════════════════════════

Upload each file as multipart/form-data using curl with -F flags.

File 1: "FInancials main/SR Papers/SRPAPERS_2023 - 24 - Updated.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2024
  - nature: audited
  - source_unit: rupees

File 2: "FInancials main/SR Papers/SRPAPERS_2024 - 25 - Updated.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2025
  - nature: audited
  - source_unit: rupees

File 3: "FInancials main/SR Papers/SRPAPERS_2025-26_-_Updated.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2026
  - nature: audited
  - source_unit: rupees

NOTE: The financial_year values match the END of the fiscal year:
- "2023-24" → financial_year: 2024
- "2024-25" → financial_year: 2025
- "2025-26" → financial_year: 2026

Save all 3 document_ids.

═══════════════════════════════════════════════════════════════
TASK 3: Trigger Extraction + Poll
═══════════════════════════════════════════════════════════════

For each document_id:
POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/extract

Poll status (max 20 polls, 5 seconds apart):
GET http://localhost:8000/api/documents/?client_id={{CLIENT_ID}}

Wait until all 3 have extraction_status = "extracted".

═══════════════════════════════════════════════════════════════
TASK 4: Check Extracted Items
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/items

Expected: 30-80 items per document. NOT 500+ (that means sheet filtering failed).
Source amounts should be in full Rupees (e.g., 339,527,844 for ~34 Cr revenue).

Key items to check for:
- Revenue from Operations (~33-36 Cr range in Rupees)
- Purchase of Stock in Trade (this is a trading company — purchases, not raw materials)
- Employee Benefits
- Depreciation
- Finance Costs
- Trade Receivables / Payables

═══════════════════════════════════════════════════════════════
TASK 5: Verify All Documents
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/verify

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

{
  "client_id": "...",
  "document_ids": ["doc1", "doc2", "doc3"],
  "items_per_doc": { "doc1": N, "doc2": N, "doc3": N },
  "extraction_notes": "any issues"
}
```

---

## SECTION B — AGENT 2 PROMPT: Classify + Review

```
You are testing the CMA Automation System with SR Papers (trading/distribution company).

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000
CLIENT_ID: {{CLIENT_ID}}
DOCUMENT_IDS: {{DOCUMENT_IDS}}

DISABLE_AUTH is true.

IMPORTANT LIMITS: Max 20 polls per document, max 100 total API calls.

═══════════════════════════════════════════════════════════════
TASK 1: Trigger Classification for All 3 Documents
═══════════════════════════════════════════════════════════════

For each document_id:
POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/classify

Monitor with: docker compose logs --tail=20 worker

═══════════════════════════════════════════════════════════════
TASK 2: Create CMA Report
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/
Body: {
  "title": "SR Papers CMA FY2024-FY2026",
  "document_ids": {{DOCUMENT_IDS}},
  "cma_output_unit": "crores"
}

Save the report_id.

═══════════════════════════════════════════════════════════════
TASK 3: Review Doubts
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/classifications

SR Papers classification hints (trading company):
- "Purchase of Stock in Trade" → R42 (Raw Materials Indigenous) — for trading companies, purchases go here
- "Revenue from Operations" → R22 (Domestic)
- "Employee Benefits" → R45 (Wages) + R67 (Salary)
- "Depreciation" → R56
- "Rent" → R68
- "Hamali / Cooly / Cartage" → R47 (Freight)
- "Finance Costs" / "Interest" → R83 (TL) or R84 (WC)
- "Audit Fee" / "Directors Remuneration" → R73
- "Trade Receivables" → R206
- "Trade Payables" → R242
- "Security Deposits" → R237 (Govt) or R238 (Private)

Correct obvious misclassifications via PATCH if API supports it.

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

{
  "report_id": "...",
  "total_classified": N,
  "high_confidence": N,
  "doubts": N,
  "classification_notes": "any issues"
}
```

---

## SECTION C — AGENT 3 PROMPT: Generate Excel + Compare

```
You are testing the CMA Automation System. Generate the CMA Excel and compare vs ground truth.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000
CLIENT_ID: {{CLIENT_ID}}
REPORT_ID: {{REPORT_ID}}

DISABLE_AUTH is true.

IMPORTANT LIMITS: Max 10 polls for generation.

═══════════════════════════════════════════════════════════════
TASK 1: Generate CMA Excel
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/generate

Poll until complete:
GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}

═══════════════════════════════════════════════════════════════
TASK 2: Download Generated File
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/download

Save to: DOCS/test-results/SRPapers_generated_CMA.xlsm

═══════════════════════════════════════════════════════════════
TASK 3: Compare Against Ground Truth
═══════════════════════════════════════════════════════════════

Ground Truth: FInancials main/SR Papers/CMA S.R.Papers 09032026 v2.xls (xlrd)
Generated: DOCS/test-results/SRPapers_generated_CMA.xlsm (openpyxl)

Both have "INPUT SHEET". Compare these cells (values in Crores):

Row | Label                              | B(2024) | C(2025) | D(2026)
----|--------------------------------------|---------|---------|--------
 22 | Domestic Sales                       |   32.66 |   33.95 |   36.32
 41 | Raw Materials (Imported)             |    0.13 |    0.06 |    0.00
 42 | Raw Materials (Indigenous)           |   23.08 |   23.64 |   25.43
 45 | Wages                                |    1.61 |    1.66 |    1.64
 47 | Freight & Transport                  |    0.16 |    0.18 |    0.19
 48 | Power, Coal, Fuel                    |    0.19 |    0.14 |    0.16
 50 | Repairs & Maintenance                |    0.18 |    0.18 |    0.15
 67 | Salary & Staff                       |    0.02 |    0.03 |    0.03
 68 | Rent, Rates & Taxes                  |    1.96 |    2.26 |    2.30
 70 | Advertisements                       |    0.14 |    0.14 |    0.17
 71 | Others (Selling)                     |    1.78 |    1.77 |    1.86
 73 | Audit Fees & Directors Remun.        |    0.50 |    0.49 |    0.49
 83 | Interest on TL                       |    0.55 |    2.00 |    2.10
 84 | Interest on WC                       |    1.28 |    1.35 |    1.40
 85 | Bank Charges                         |    1.02 |    0.00 |    0.01
 99 | Income Tax Provision                 |    0.01 |    0.01 |    0.03
116 | Share Capital                        |    0.20 |    0.20 |    0.20
152 | Quasi Equity                         |    8.80 |   11.59 |   16.44
162 | Gross Block                          |   16.95 |   17.41 |   17.22
206 | Domestic Receivables                 |    5.10 |    5.08 |    5.87
212 | Cash on Hand                         |    0.42 |    0.47 |    0.50
237 | Security Deposits (Govt)             |    1.71 |    3.78 |    3.95
242 | Sundry Creditors                     |    3.92 |    5.40 |    5.57

Tolerance: 2% (accounts for rounding).

═══════════════════════════════════════════════════════════════
TASK 4: Verify Template Structure
═══════════════════════════════════════════════════════════════

Check:
1. Row 7: Client name = "SR Papers"
2. Row 8: Years = B:2024, C:2025, D:2026, E:2027, F:2028, G:2029, H:2030
3. Row 10: B-D = Audited, E-H = Projected
4. File is .xlsm with macros
5. Column E-H formulas preserved

═══════════════════════════════════════════════════════════════
TASK 5: Save Test Results
═══════════════════════════════════════════════════════════════

Create DOCS/test-results/SRPapers_test_results.md with full results.

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

{
  "cells_checked": N,
  "matching": N,
  "mismatched": N,
  "missing": N,
  "accuracy_pct": N,
  "file_saved": "DOCS/test-results/SRPapers_generated_CMA.xlsm",
  "results_saved": "DOCS/test-results/SRPapers_test_results.md"
}
```

---

## AFTER ALL AGENTS COMPLETE

Compile the final results showing extraction, classification, and Excel accuracy.
