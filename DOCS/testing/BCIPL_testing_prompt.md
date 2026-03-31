# BCIPL (Bagadia Chaitra Industries) — Agent-Team App Verification

**Purpose:** Paste this into a fresh Claude Code session. It will deploy **3 focused agents** sequentially, each handling one phase. No code changes needed — all fixes are already applied.

**Priority:** The #1 goal is verifying the generated CMA Excel has the correct numbers in the correct cells.

---

## COMPANY DETAILS

| Field | Value |
|-------|-------|
| Company | Bagadia Chaitra Industries Private Limited (BCIPL) |
| Industry | Manufacturing — Metal Stamping / Laminations |
| Source Files | 3 x `.xls` (Excel 97) in `FInancials main/BCIPL/` |
| Ground Truth CMA | `FInancials main/BCIPL/CMA BCIPL 12012024.xls` |
| Source Unit | Full Rupees (`rupees`) |
| CMA Output Unit | Crores (`crores`) — divisor = 10,000,000 |
| Financial Years | FY2021 (col B), FY2022 (col C), FY2023 (col D) |
| Nature | All Audited |

---

## HOW THIS WORKS

You are the **orchestrator**. You deploy agents for each phase:

```
STEP 0: Pre-flight (YOU do this, no agent)
    - Run DB migration
    - Start Docker
    - Health check
    ↓
AGENT 1: Upload + Extract + Verify
    ↓ passes client_id, document_ids
AGENT 2: Classify + Review doubts
    ↓ passes report_id
AGENT 3: Generate Excel + Compare vs ground truth
    ↓ saves file to DOCS/test-results/
```

**IMPORTANT orchestration rules:**
- Deploy agents ONE AT A TIME (each depends on the previous)
- After Agent 1, extract `client_id` and `document_ids` from its result and pass to Agent 2
- After Agent 2, extract `report_id` and pass to Agent 3
- After Agent 3, compile the final test report yourself
- **NEVER** create unbounded loops — max 20 polls, max 100 API calls per agent
- **NEVER** retry failed API calls more than 3 times

---

## STEP 0: Pre-flight (YOU do this)

### 0a. Run DB Migration
Go to Supabase Dashboard > SQL Editor > New Query, and run:

```sql
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS source_unit TEXT
  DEFAULT 'rupees'
  CHECK (source_unit IN ('rupees', 'thousands', 'lakhs', 'crores'));

ALTER TABLE cma_reports
  ADD COLUMN IF NOT EXISTS cma_output_unit TEXT
  DEFAULT 'lakhs'
  CHECK (cma_output_unit IN ('lakhs', 'crores'));
```

### 0b. Start Docker
```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 0c. Health Check
```bash
curl http://localhost:8000/health
docker compose ps
```
Verify all 4 services are up: backend, frontend, worker, redis.

---

## SECTION A — AGENT 1 PROMPT: Upload + Extract + Verify

```
You are testing the CMA Automation System. Your task is to upload 3 BCIPL financial documents, trigger extraction, and verify the results.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000

DISABLE_AUTH is true — use any user_id for auth. Get a dev session first.

IMPORTANT LIMITS: Max 20 API polls, max 3 retries per call. If extraction takes more than 2 minutes per doc, something is wrong — report it and stop.

═══════════════════════════════════════════════════════════════
TASK 1: Create Client
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/
Body: { "name": "BCIPL", "industry_type": "manufacturing" }

Save the client_id from the response.

═══════════════════════════════════════════════════════════════
TASK 2: Upload 3 Documents
═══════════════════════════════════════════════════════════════

Upload each file as multipart/form-data:

File 1: "FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2021
  - nature: audited
  - source_unit: rupees

File 2: "FInancials main/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2022
  - nature: audited
  - source_unit: rupees

File 3: "FInancials main/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls"
  - client_id: {{CLIENT_ID}}
  - document_type: combined_financial_statement
  - financial_year: 2023
  - nature: audited
  - source_unit: rupees

Use curl with -F flags. Example:
curl -X POST http://localhost:8000/api/documents/ \
  -F "client_id={{CLIENT_ID}}" \
  -F "document_type=combined_financial_statement" \
  -F "financial_year=2021" \
  -F "nature=audited" \
  -F "source_unit=rupees" \
  -F "file=@FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls"

Save all 3 document_ids.

═══════════════════════════════════════════════════════════════
TASK 3: Trigger Extraction
═══════════════════════════════════════════════════════════════

For each document_id, trigger extraction:
POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/extract

Then poll extraction status (max 20 polls, 5 seconds apart):
GET http://localhost:8000/api/documents/?client_id={{CLIENT_ID}}

Wait until all 3 documents have extraction_status = "extracted".

═══════════════════════════════════════════════════════════════
TASK 4: Check Extracted Items
═══════════════════════════════════════════════════════════════

For each document, get the extracted line items:
GET http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/items

Check:
- Each document should have 30-100 line items (not 500+ — that means sheet filtering failed)
- Key items should be present: Revenue, Raw Materials, Wages, Depreciation, Interest, Share Capital, Debtors, Creditors
- Amounts should be in full Rupees (large numbers like 10,00,000 to 50,00,00,000)

Report the count per document.

═══════════════════════════════════════════════════════════════
TASK 5: Verify All Documents
═══════════════════════════════════════════════════════════════

For each document, approve all extracted items:
POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/verify

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

Return a JSON block with:
{
  "client_id": "...",
  "document_ids": ["doc1", "doc2", "doc3"],
  "items_per_doc": { "doc1": 45, "doc2": 52, "doc3": 61 },
  "extraction_notes": "any issues found"
}
```

---

## SECTION B — AGENT 2 PROMPT: Classify + Review

```
You are testing the CMA Automation System. Your task is to classify all extracted items for 3 BCIPL documents, review doubts, and create a CMA report.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000
CLIENT_ID: {{CLIENT_ID}}
DOCUMENT_IDS: {{DOCUMENT_IDS}}

DISABLE_AUTH is true.

IMPORTANT LIMITS: Max 20 polls per document, max 100 total API calls. Classification may take 1-3 minutes per document (AI model processes each item). If it takes more than 5 minutes per doc, something is wrong — check worker logs with: docker compose logs --tail=50 worker

═══════════════════════════════════════════════════════════════
TASK 1: Trigger Classification for All 3 Documents
═══════════════════════════════════════════════════════════════

For each document_id:
POST http://localhost:8000/api/extraction/{{DOCUMENT_ID}}/classify

Then poll status until all are classified. Check worker logs if slow:
docker compose logs --tail=20 worker

═══════════════════════════════════════════════════════════════
TASK 2: Check Classification Results
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/

If no report exists yet, check classifications directly.
Get the confidence summary — how many high confidence, medium, doubts?

═══════════════════════════════════════════════════════════════
TASK 3: Create CMA Report
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/
Body: {
  "title": "BCIPL CMA FY2021-FY2023",
  "document_ids": {{DOCUMENT_IDS}},
  "cma_output_unit": "crores"
}

Save the report_id.

═══════════════════════════════════════════════════════════════
TASK 4: Review Doubts (if any)
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/classifications

Look at items where is_doubt=true. For obvious matches, correct them:
- "Revenue from Operations" → R22 (Domestic Sales)
- "Cost of Raw Materials Consumed" → R42 (Raw Materials Indigenous)
- "Employee Benefits Expense" → R45 (Wages) + R67 (Salary)
- "Depreciation" → R56
- "Finance Costs" → R83/R84 (Interest on TL / WC)
- "Trade Receivables" → R206 (Domestic Receivables)
- "Trade Payables" → R242 (Sundry Creditors)

Use PATCH to correct classifications if the API supports it.
If too many doubts (>50%), note this as an issue but proceed.

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

{
  "report_id": "...",
  "total_classified": 150,
  "high_confidence": 80,
  "medium_confidence": 30,
  "doubts": 40,
  "doubts_corrected": 15,
  "classification_notes": "any issues"
}
```

---

## SECTION C — AGENT 3 PROMPT: Generate Excel + Compare

```
You are testing the CMA Automation System. Your task is to generate the CMA Excel file and compare it cell-by-cell against the ground truth.

PROJECT ROOT: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
API BASE: http://localhost:8000
CLIENT_ID: {{CLIENT_ID}}
REPORT_ID: {{REPORT_ID}}

DISABLE_AUTH is true.

IMPORTANT LIMITS: Max 10 polls for generation status. If generation fails, check worker logs: docker compose logs --tail=50 worker

═══════════════════════════════════════════════════════════════
TASK 1: Generate CMA Excel
═══════════════════════════════════════════════════════════════

POST http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/generate

Poll until status = "completed" or "generated":
GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}

═══════════════════════════════════════════════════════════════
TASK 2: Download the Generated File
═══════════════════════════════════════════════════════════════

GET http://localhost:8000/api/clients/{{CLIENT_ID}}/cma-reports/{{REPORT_ID}}/download

Save the response (it returns a signed URL). Download the file and save to:
DOCS/test-results/BCIPL_generated_CMA.xlsm

If the download API returns a URL, use curl to download:
curl -L "{{SIGNED_URL}}" -o "DOCS/test-results/BCIPL_generated_CMA.xlsm"

═══════════════════════════════════════════════════════════════
TASK 3: Compare Against Ground Truth
═══════════════════════════════════════════════════════════════

Write a Python script that compares the generated CMA vs ground truth.
Save the script to: test-results/compare_bcipl_cma.py

Ground Truth file: FInancials main/BCIPL/CMA BCIPL 12012024.xls (use xlrd to read .xls)
Generated file: DOCS/test-results/BCIPL_generated_CMA.xlsm (use openpyxl to read .xlsm)

Both files have an "INPUT SHEET" worksheet.

Compare these specific cells (Row, Col B/C/D = FY2021/2022/2023):

GROUND TRUTH VALUES (in Crores):
Row | Label                                    | B(2021) | C(2022) | D(2023)
----|------------------------------------------|---------|---------|--------
 22 | Domestic Sales                           |   96.58 |  234.64 |  256.95
 23 | Exports                                  |    8.86 |    2.44 |    7.44
 42 | Raw Materials (Indigenous)               |   84.35 |  196.50 |  217.74
 44 | Stores and Spares (Indigenous)           |    1.76 |    3.49 |    4.39
 45 | Wages                                    |    6.38 |   10.32 |   12.53
 46 | Processing/Job Work                      |    1.22 |    2.05 |    2.26
 48 | Power, Coal, Fuel                        |    0.80 |    0.98 |    1.22
 50 | Repairs & Maintenance                    |    —    |    0.22 |    0.42
 67 | Salary & Staff                           |    0.30 |    1.66 |    1.25
 68 | Rent, Rates & Taxes                      |    0.10 |    0.09 |    0.07
 70 | Advertisements & Sales Promotions        |    —    |    3.21 |    6.78
 71 | Others (Selling)                         |    2.31 |    3.38 |    1.68
 83 | Interest on TL                           |    1.30 |    1.47 |    1.43
 84 | Interest on WC                           |    0.65 |    1.27 |    2.59
 85 | Bank Charges                             |    0.09 |    0.15 |    0.17
 99 | Income Tax Provision                     |    0.02 |    2.20 |    1.76
116 | Share Capital                            |    3.09 |    3.09 |    3.09
136 | TL Repayable in 1 year                   |    3.00 |    4.12 |    5.05
137 | TL Balance after 1 year                  |   16.68 |   12.76 |    6.32
152 | Quasi Equity                             |    4.13 |    4.13 |    4.13
162 | Gross Block                              |   45.90 |   49.86 |   53.19
206 | Domestic Receivables                     |   17.92 |   34.70 |   15.48
212 | Cash on Hand                             |    0.01 |    0.01 |    0.01
242 | Sundry Creditors                         |   10.31 |   12.79 |   14.29

For each cell:
- MATCH: generated value is within 2% of ground truth (or both are 0)
- MISMATCH: values differ by more than 2%
- MISSING: ground truth has value but generated is 0 or empty

Tolerance of 2% accounts for rounding differences.

═══════════════════════════════════════════════════════════════
TASK 4: Verify Template Structure
═══════════════════════════════════════════════════════════════

Check the generated file for:
1. Row 7: Client name = "BCIPL"
2. Row 8: Years = B:2021, C:2022, D:2023, E:2024, F:2025, G:2026, H:2027
3. Row 10: Nature = B:Audited, C:Audited, D:Audited, E-H:Projected
4. File extension is .xlsm (macros preserved)
5. Column E-H should have projection formulas (not overwritten)

═══════════════════════════════════════════════════════════════
TASK 5: Save Test Results
═══════════════════════════════════════════════════════════════

Create DOCS/test-results/BCIPL_test_results.md with:
- Company details
- IDs used (client_id, document_ids, report_id)
- Extraction summary (items per doc)
- Classification summary (confidence breakdown)
- Cell comparison table (match/mismatch/missing for each row)
- Overall accuracy percentage
- Bugs found
- Priority fixes needed

═══════════════════════════════════════════════════════════════
RETURN THIS DATA:
═══════════════════════════════════════════════════════════════

{
  "cells_checked": 72,
  "matching": 55,
  "mismatched": 10,
  "missing": 7,
  "accuracy_pct": 76.4,
  "file_saved": "DOCS/test-results/BCIPL_generated_CMA.xlsm",
  "results_saved": "DOCS/test-results/BCIPL_test_results.md",
  "bugs_found": ["list of any bugs"]
}
```

---

## AFTER ALL AGENTS COMPLETE

Compile the final results into a summary message showing:
1. Extraction: items per document
2. Classification: confidence breakdown
3. Excel accuracy: X/Y cells correct (Z%)
4. Top issues found
5. Comparison with MSL test (if applicable)
