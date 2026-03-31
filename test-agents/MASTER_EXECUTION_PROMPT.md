# CMA Automation System — Master Test Execution Instructions

> **READ THIS FIRST — CRITICAL**
> This document is the single source of truth for the entire test run.
> You are the ORCHESTRATOR. Do NOT re-plan, do NOT redesign agents.
> Execute exactly what is described here, in the exact order specified.
> When in doubt: follow the file, not your instincts.

---

## 1. WHO YOU ARE AND WHAT YOU DO

You are the **Orchestrator (Agent 0)**. Your job:
1. Read this file completely before doing anything
2. Execute agents in tier order, enforcing gates
3. Each agent you spawn writes its results to a file — you never hold large results in your context
4. After all agents complete, assemble `test-results/TEST_REPORT.md` by reading each agent's output file
5. Show the user a concise summary with a link to the full report

**Context window discipline (non-negotiable):**
- Every agent writes its full output to `test-results/agentN-*.md` or `.json`
- You only track: agent name + pass/fail + output file path
- You never read an agent's full output into this conversation — only the summary line
- The final report is assembled by reading all files at the end, not from memory

---

## 2. SYSTEM STATE (DO NOT CHANGE THESE)

```
Docker:         All 3 containers running
  backend:      http://localhost:8000
  frontend:     http://localhost:3002
  redis:        localhost:6379

Auth:           DISABLE_AUTH=true in .env
                Mock admin user active (no real login needed for most agents)
                Mock user: id=00000000-0000-0000-0000-000000000001, role=admin

Real test user: email=admin@cma.test  password=CmaAdmin@2024  role=admin
                (Only for Agent 2 security tests — requires DISABLE_AUTH=false temporarily)

Project root:   C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
Backend port:   8000
Frontend port:  3002
```

---

## 3. DOCUMENT MANIFEST (LOCKED — DO NOT DEVIATE)

### Company: Mehta Computers
**Industry: TRADING** (buys and resells computer hardware/software — confirmed from financial data showing purchases for resale classified as raw materials, zero factory wages, zero manufacturing headcount)

**Base path:** `C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\Excel_project\Mehta computer\`

#### Documents to USE for extraction testing:

| File | Location | Content | Financial Year |
|------|----------|---------|----------------|
| `Mehta_Computers_financials_2022.xls` | Inside `2022.zip` | P&L + Balance Sheet | FY 2021-22 (Audited) |
| `Mehta Computers financials 2023.xls` | Inside `2023.zip` | P&L + Balance Sheet | FY 2022-23 (Audited) |
| `Mehta_Computers_financials_2024.xls` | Inside `2024.zip` | P&L + Balance Sheet | FY 2023-24 (Audited) |
| `BSheet.pdf` | `2025/` folder | Balance Sheet | FY 2024-25 (Provisional) |
| `PandL.pdf` | `2025/` folder | Profit & Loss | FY 2024-25 (Provisional) |
| `TrialBal.pdf` | `2025/` folder | Trial Balance | FY 2024-25 (Provisional) |
| `EMI Schedule.pdf` | Root of Mehta folder | Loan repayment schedule | (for TL Sheet) |

**Extraction order:** Start with `Mehta_Computers_financials_2024.xls` (most recent audited, clean Excel format) as the primary test document. Then test `PandL.pdf` for PDF extraction path.

#### Ground Truth CMA (Agent 5 only):
```
File:    CMA 15092025.xls
Path:    Mehta computer\CMA 15092025.xls
Sheet:   INPUT SHEET
Columns: B=FY2022, C=FY2023, D=FY2024, E=FY2025(Provisional)
```

**Known correct values in ground truth (use these to validate extraction AND classification):**

| Row | CMA Field | FY2022 | FY2023 | FY2024 | FY2025 |
|-----|-----------|--------|--------|--------|--------|
| R21 | Domestic Sales | 182.5508 | 327.00628 | 230.61052 | 519.5032827 |
| R22 | Export Sales | 0.0 | 0.0 | 0.0 | 0.0 |
| R41 | Raw Materials Consumed (Indigenous) | 162.92324 | 308.65095 | 174.12563 | 470.3608089 |
| R47 | Power, Coal, Fuel and Water | 0.13688 | 0.0732 | 0.26692 | 0.29367 |
| R55 | Depreciation (Manufacturing) | 0.11122 | 0.14166 | 0.13084 | 0.11122 |
| R66 | Salary and staff expenses | 5.2385 | 5.93892 | 14.86331 | 13.67577 |
| R67 | Rent, Rates and Taxes | 0.342 | 0.444 | 0.444 | 0.444 |
| R69 | Advertisements and Sales Promotions | 2.349314 | 10.639467 | 6.432721 | 14.201703 |
| R82 | Interest on Fixed Loans / Term loans | 1.90188 | 1.65273 | 1.28496 | 8.07102 |
| R84 | Bank Charges | 0.0096524 | 0.0101546 | 0.0312659 | 0.0060756 |

#### Documents to SKIP (do not upload to app):
- `ITR one page 21-22.jpeg` — tax form image, not financial statements
- `ITR one page 22-23.jpeg` — tax form image
- `ITR one page 23-24.jpeg` — tax form image
- `ITR Acknowledgement FY 22-23.pdf` — tax filing confirmation, not financial data
- `ITR Intimation FY 2023-24.pdf` — tax filing notice, not financial data
- `Wankaner - Letter.pdf` — business letter, not financial data

#### Unknown — check during Agent 0.5:
- `MyData.xls` and `MyData.xlsm` in `DOCS/Excel_project/` root
  - These have CMA template structure with years 2023/2024/2025
  - Check: does the INPUT SHEET have a company name in R6 col B?
  - If it has a real company name (not "Test" or blank): treat as Company 2 and add to extraction test
  - If blank or "Test": it's dev test data, skip it

#### CMA Template:
```
Path:   C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\CMA.xlsm
        OR DOCS\Excel_project\CMA.xlsm (check both, use whichever exists)
Purpose: Agent 6 downloads generated output and compares structure against this template
```

---

## 4. OUTPUT FILE STRUCTURE

All agents write here. Create these paths if they don't exist:

```
C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\
  test-results\
    agent05-manifest.json       ← Agent 0.5 output
    agent1-health.json          ← Agent 1 output
    agent2-security.md          ← Agent 2 output
    agent3-api.md               ← Agent 3 output
    agent4-extraction.md        ← Agent 4 output
    agent5-classification.md    ← Agent 5 output (largest, most important)
    agent6-excel.md             ← Agent 6 output
    agent7-e2e\
      log.md                    ← Agent 7 pass/fail log
      step-01-login.png         ← Screenshots (one per step)
      step-02-dashboard.png
      ... (steps 01-15)
    agent8-chaos.md             ← Agent 8 output
    TEST_REPORT.md              ← Final assembled report (Agent 0 writes this last)
```

---

## 5. EXECUTION FLOW AND GATES

```
START
  │
  ▼
[Agent 0.5] Document Intelligence
  │  Writes: agent05-manifest.json
  │  No gate — always runs
  ▼
[Agent 1] Infrastructure Health  ◄── GATE 1
  │  Writes: agent1-health.json
  │  ALL checks must pass → if ANY fail, STOP and report to user
  ▼
[Agent 2] Auth & Security   ┐  (spawn both in parallel)
[Agent 3] API Contract      ┘
  │  Both write their output files
  │  Gate 2: Agent 3 must pass (Agent 2 failures are findings, not blockers)
  ▼
[Agent 4] Extraction Pipeline  ◄── GATE 3: needs working API from Agent 3
  │  Writes: agent4-extraction.md
  │  Must successfully extract items → if extraction fails, STOP
  ▼
[Agent 5] Classification Quality Judge
  │  Writes: agent5-classification.md
  │  Must complete comparison → findings are non-blocking
  ▼
[Agent 6] Excel Validator     ┐  (spawn both in parallel)
[Agent 7] E2E Playwright      ┘
  │  Both write their output files
  ▼
[Agent 8] Chaos Monkey
  │  Writes: agent8-chaos.md
  ▼
[Agent 0] Assembles TEST_REPORT.md
  │  Reads all output files
  │  Writes final report
  ▼
END — show user: "Testing complete. Report at test-results/TEST_REPORT.md"
```

---

## 6. AGENT INSTRUCTIONS (ONE BY ONE)

---

### AGENT 0.5 — Document Intelligence

**Purpose:** Identify which documents are financial statements, confirm company details, flag what to skip.

**Inputs:**
- `DOCS/Excel_project/Mehta computer/` folder (all contents including zip files)
- `DOCS/Excel_project/MyData.xls` and `MyData.xlsm`

**Steps:**
1. Extract each zip file temporarily to read contents:
   - `2022.zip` → find `Mehta_Computers_financials_2022.xls`
   - `2023.zip` → find `Mehta Computers financials 2023.xls`
   - `2024.zip` → find `Mehta_Computers_financials_2024.xls`
2. Open `Mehta_Computers_financials_2024.xls` with xlrd/openpyxl. Read sheet names and first 10 rows of each sheet. Identify: company name, financial year, whether it has P&L + Balance Sheet sections.
3. Open `MyData.xls`. Read `INPUT SHEET` row 6 col B — is there a company name? Report what you find.
4. Open `CMA 15092025.xls`. Confirm it has `INPUT SHEET` with company name "Mehta Computers" and 4 years of data (2022–2025). Confirm it is the completed CMA (has numeric values in rows 21–108 and rows 116–258).
5. Identify industry from financial content: look for keywords like "raw materials", "factory wages", "manufacturing" vs "purchases for resale", "trading stock", "goods sold". Report: Manufacturing / Service / Trading.

**Output — write to `test-results/agent05-manifest.json`:**
```json
{
  "company_name": "Mehta Computers",
  "industry": "Trading",
  "financial_years": ["FY2022", "FY2023", "FY2024", "FY2025"],
  "documents_to_use": [
    {"file": "Mehta_Computers_financials_2022.xls", "source": "2022.zip", "year": "FY2022", "type": "Excel", "content": "P&L + Balance Sheet"},
    {"file": "Mehta Computers financials 2023.xls",  "source": "2023.zip", "year": "FY2023", "type": "Excel", "content": "P&L + Balance Sheet"},
    {"file": "Mehta_Computers_financials_2024.xls", "source": "2024.zip", "year": "FY2024", "type": "Excel", "content": "P&L + Balance Sheet"},
    {"file": "BSheet.pdf",  "source": "2025/", "year": "FY2025", "type": "PDF", "content": "Balance Sheet"},
    {"file": "PandL.pdf",   "source": "2025/", "year": "FY2025", "type": "PDF", "content": "P&L"},
    {"file": "TrialBal.pdf","source": "2025/", "year": "FY2025", "type": "PDF", "content": "Trial Balance"},
    {"file": "EMI Schedule.pdf", "source": "root", "year": "multi", "type": "PDF", "content": "TL loan repayment"}
  ],
  "documents_skipped": [
    {"file": "ITR one page 21-22.jpeg", "reason": "Tax form image, not financial statement"},
    {"file": "ITR one page 22-23.jpeg", "reason": "Tax form image"},
    {"file": "ITR one page 23-24.jpeg", "reason": "Tax form image"},
    {"file": "ITR Acknowledgement FY 22-23.pdf", "reason": "Tax filing confirmation"},
    {"file": "ITR Intimation FY 2023-24.pdf", "reason": "Tax filing notice"},
    {"file": "Wankaner - Letter.pdf", "reason": "Business letter"}
  ],
  "mydata_assessment": "DESCRIBE WHAT YOU FOUND — company name or blank?",
  "ground_truth_cma": {
    "file": "CMA 15092025.xls",
    "sheet": "INPUT SHEET",
    "columns": {"B": "FY2022", "C": "FY2023", "D": "FY2024", "E": "FY2025"},
    "confirmed_populated": true
  }
}
```

**Pass criteria:** Manifest written, at least 4 financial documents identified, ground truth CMA confirmed.

---

### AGENT 1 — Infrastructure Health Check

**Purpose:** Confirm every service is alive before any real tests run. This is the GATE — nothing proceeds if this fails.

**Inputs:** None (just hit the known endpoints)

**Steps — run each check, record pass/fail:**

1. **Docker containers:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   ```
   Expected: `cmaproject-2-backend-1`, `cmaproject-2-frontend-1`, `cmaproject-2-redis-1` all showing `Up`

2. **Backend health:**
   ```
   GET http://localhost:8000/health
   Expected: 200 OK, body contains {"status": "ok"} or similar
   ```

3. **Backend OpenAPI (all routes registered):**
   ```
   GET http://localhost:8000/docs
   Expected: 200, HTML page loads (FastAPI docs)
   GET http://localhost:8000/openapi.json
   Expected: 200, JSON with "paths" key containing at least 15 routes
   ```

4. **Frontend loads:**
   ```
   GET http://localhost:3002
   Expected: 200 (or 307 redirect to /login or /dashboard), HTML with Next.js content
   ```

5. **Supabase reference data:**
   Hit `GET http://localhost:8000/api/clients` (DISABLE_AUTH=true, no token needed)
   Check backend is connecting to Supabase by confirming it returns 200 (not 500/502).
   Then directly query via Python supabase client:
   ```python
   from supabase import create_client
   url = "https://sjdzmkqfsehfpptxoxca.supabase.co"
   key = "<SUPABASE_ANON_KEY from .env>"
   # Use service role key from .env for this check
   # Count rows in cma_reference_mappings
   # Expected: 384-387 rows
   ```

6. **Redis / ARQ worker:**
   ```bash
   docker exec cmaproject-2-redis-1 redis-cli ping
   Expected: PONG
   ```
   Also check backend logs for ARQ worker connection:
   ```bash
   docker logs cmaproject-2-backend-1 --tail 20
   ```
   Look for: no Redis connection errors

7. **Anthropic API key set:**
   Check `.env` file — `ANTHROPIC_API_KEY` must not be empty.
   DO NOT log the actual key value — just check it is non-empty.

**Output — write to `test-results/agent1-health.json`:**
```json
{
  "overall": "PASS",
  "checks": {
    "docker_backend": "PASS",
    "docker_frontend": "PASS",
    "docker_redis": "PASS",
    "backend_health": "PASS",
    "backend_openapi": "PASS",
    "frontend_loads": "PASS",
    "supabase_reference_data": "PASS / count: 385",
    "redis_ping": "PASS",
    "arq_worker": "PASS",
    "anthropic_key_set": "PASS"
  },
  "failures": [],
  "notes": "any relevant observations"
}
```

**GATE 1 RULE:** If `overall` is not PASS (any single check fails), write the failure to the file, then STOP and tell the user exactly which check failed and what they need to fix. Do NOT proceed to Agents 2–8.

---

### AGENT 2 — Auth & Security Tester

**Purpose:** Verify the security layer is solid. Runs WITH real auth (DISABLE_AUTH=false temporarily).

**IMPORTANT — Before starting:**
1. Read current `.env` file content
2. Temporarily set `DISABLE_AUTH=false` (edit the file)
3. Restart backend only: `docker compose restart backend`
4. Wait for backend to be healthy (GET /health → 200)
5. Run all tests
6. **RESTORE** `DISABLE_AUTH=true` when done
7. Restart backend again: `docker compose restart backend`

**Test user credentials:** `email=admin@cma.test  password=CmaAdmin@2024`

**Steps — run each, record result:**

1. **Valid login returns JWT:**
   ```
   POST http://localhost:8000/api/auth/login
   Body: {"email": "admin@cma.test", "password": "CmaAdmin@2024"}
   Expected: 200, body has "access_token" field (non-empty string)
   Save the token as VALID_TOKEN for subsequent tests
   ```

2. **Wrong password returns 401:**
   ```
   POST /api/auth/login
   Body: {"email": "admin@cma.test", "password": "wrongpassword"}
   Expected: 401
   Verify: response body does NOT contain the word "token"
   ```

3. **No token returns 401:**
   ```
   GET /api/clients (no Authorization header)
   Expected: 401
   ```

4. **Malformed token returns 401:**
   ```
   GET /api/clients
   Header: Authorization: Bearer thisisnotavalidtoken
   Expected: 401
   ```

5. **Employee cannot access admin routes:**
   First create an employee user:
   ```
   POST /api/auth/register
   Header: Authorization: Bearer {VALID_TOKEN}
   Body: {"email": "employee@cma.test", "password": "Employee@2024", "full_name": "Test Employee", "role": "employee"}
   Expected: 201
   ```
   Then login as employee:
   ```
   POST /api/auth/login
   Body: {"email": "employee@cma.test", "password": "Employee@2024"}
   Save as EMPLOYEE_TOKEN
   ```
   Then try admin-only route:
   ```
   DELETE /api/clients/{any_id}
   Header: Authorization: Bearer {EMPLOYEE_TOKEN}
   Expected: 403
   ```

6. **File upload path traversal rejected:**
   ```
   POST /api/documents/upload (multipart)
   filename: "../../etc/passwd.pdf"
   Content-Type: application/pdf
   Expected: Either 400 (rejected) OR filename sanitized (no path traversal stored)
   FAIL if: server returns 500 or if filename stored verbatim with ../
   ```

7. **Non-PDF/Excel file rejected:**
   ```
   POST /api/documents/upload
   filename: "malware.exe"
   Content-Type: application/octet-stream
   Expected: 400 with error message about invalid file type
   ```

8. **CORS — unauthorized origin blocked:**
   ```
   Send request with Origin: http://evil.com
   Expected: No Access-Control-Allow-Origin: http://evil.com in response
   ```

**ALWAYS restore DISABLE_AUTH=true after this agent, regardless of test outcomes.**

**Output — write to `test-results/agent2-security.md`:**
```markdown
# Agent 2: Auth & Security Report

## Overall: PASS/FAIL

| Test | Result | Notes |
|------|--------|-------|
| Valid login returns JWT | PASS/FAIL | ... |
| Wrong password → 401 | PASS/FAIL | ... |
...

## Issues Found
### CRITICAL (must fix before production)
### HIGH
### MEDIUM
### LOW
```

**Non-blocking:** Agent 2 failures are security findings but do NOT stop the test suite. Record and continue.

---

### AGENT 3 — API Contract Tester

**Purpose:** Verify all REST endpoints exist, accept correct inputs, return correct shapes, handle errors properly.

**Auth:** DISABLE_AUTH=true is active — no token needed. All requests go to http://localhost:8000

**Setup:** Create one test client before running endpoint tests:
```
POST /api/clients
Body: {"name": "Test Client API", "industry": "Trading", "contact_person": "Test User", "contact_email": "test@test.com"}
Expected: 201, save returned "id" as CLIENT_ID
```

**Endpoint tests to run:**

**Clients:**
- `GET /api/clients` → 200, returns array
- `GET /api/clients?search=Test` → 200, returns filtered array
- `GET /api/clients/{CLIENT_ID}` → 200, has "id", "name", "industry" fields
- `GET /api/clients/nonexistent-uuid` → 404 (not 500)
- `POST /api/clients` with missing "name" → 422 (validation error, not 500)
- `PUT /api/clients/{CLIENT_ID}` with `{"name": "Updated Name"}` → 200
- `DELETE /api/clients/{CLIENT_ID}` → 200 or 204

**Documents:**
- `POST /api/documents/upload` with valid PDF → 201 (or 200), has document "id" and "status"
  - Use any small test PDF (create a tiny one-line PDF for this)
  - Required fields: file + document_type + financial_year + client_id
- `GET /api/documents?client_id={CLIENT_ID}` → 200, returns array
- `DELETE /api/documents/{doc_id}` → 200 or 204

**CMA Reports:**
- `POST /api/cma-reports` with valid client_id → 201, has "id" and "status"
  - Save as REPORT_ID
- `GET /api/cma-reports` → 200, returns array
- `GET /api/cma-reports/{REPORT_ID}` → 200, has "id", "status", "client_id"
- `GET /api/cma-reports/nonexistent` → 404

**Extraction:**
- `POST /api/extraction/trigger` with valid document_id → 200 or 202 (task enqueued)
- `GET /api/tasks/{task_id}` → 200, has "status" field

**Error format consistency:**
- All 404 responses must have: `{"detail": "...message..."}` (not raw Python traceback)
- All 422 responses must have: `{"detail": [{"loc": [...], "msg": "..."}]}`
- No endpoint should return 500 for bad user input

**Output — write to `test-results/agent3-api.md`:**
```markdown
# Agent 3: API Contract Report

## Overall: PASS/FAIL (N/M endpoints passed)

| Endpoint | Method | Expected Status | Got | Schema Valid | Result |
|----------|--------|-----------------|-----|--------------|--------|
| /api/clients | GET | 200 | 200 | ✅ | PASS |
...

## Failed Tests
## Schema Violations
## Notes
```

**GATE 2 RULE:** If more than 3 endpoints return 500 (server error) for valid inputs, STOP and report. The pipeline tests (Agents 4–8) cannot run if the API is fundamentally broken.

---

### AGENT 4 — Extraction Pipeline Tester

**Purpose:** Test document extraction with Mehta Computers' real financial files. This tests the core data pipeline.

**Prerequisites:** Agent 3 passed. CLIENT_ID from Agent 3 (or create a new client if needed).

**Primary test document:** `Mehta_Computers_financials_2024.xls` (extract from `2024.zip` first)

**Steps:**

1. **Setup — create client and prepare document:**
   ```
   POST /api/clients
   Body: {"name": "Mehta Computers Test", "industry": "Trading", "contact_person": "Test", "contact_email": "test@test.com"}
   Save CLIENT_ID
   ```

2. **Upload the Excel financial file:**
   ```
   POST /api/documents/upload (multipart)
   Fields:
     file: Mehta_Computers_financials_2024.xls (extracted from 2024.zip)
     client_id: {CLIENT_ID}
     document_type: "balance_sheet_pnl"  (or whatever the app accepts — check OpenAPI)
     financial_year: "2024"
   Expected: 201, document record with status="pending" or "uploaded"
   Save DOCUMENT_ID
   ```

3. **Trigger extraction:**
   ```
   POST /api/extraction/trigger
   Body: {"document_id": "{DOCUMENT_ID}"}
   Expected: 200/202, task_id returned
   Save TASK_ID
   ```

4. **Poll for completion (max 120 seconds, every 5 seconds):**
   ```
   GET /api/tasks/{TASK_ID}
   Poll until status = "completed" or "failed"
   Record: total time taken
   If "failed": record error message, note as EXTRACTION_FAILED
   ```

5. **Check extracted items:**
   ```
   GET /api/extraction/items?document_id={DOCUMENT_ID}
   OR GET /api/documents/{DOCUMENT_ID}/items
   (check OpenAPI for correct endpoint)
   Expected: array of line items, each with: "description", "amount", "section"
   ```
   Validate:
   - At least 10 items extracted (a real P&L + BS should have 30+)
   - Items have numeric amounts (not null/empty)
   - At least one item with "Sales" or "Revenue" in description
   - At least one item with "Capital" or "Assets" in description
   - Indian number format handled: amounts like 182.55 (lakhs) present

6. **Verify bypass test (CRITICAL):**
   ```
   Without completing verification:
   POST /api/classification/trigger
   Body: {"document_id": "{DOCUMENT_ID}"}
   Expected: 400 or 403 with message about verification required
   FAIL if: classification starts without verification
   ```

7. **Complete verification:**
   ```
   POST /api/extraction/verify
   Body: {"document_id": "{DOCUMENT_ID}", "confirmed": true}
   OR POST /api/extraction/{DOCUMENT_ID}/verify
   Expected: 200, status changes to "verified"
   ```

8. **Secondary test — PDF extraction (if primary Excel succeeded):**
   Upload `PandL.pdf` from the `2025/` folder.
   Trigger extraction. Check: does it extract line items from PDF?
   Record: how many items extracted vs Excel path.

**Record for the output file:**
- Total items extracted from Excel
- Total items extracted from PDF (if tested)
- Extraction time (seconds)
- Indian number format: handled correctly?
- Verification bypass: blocked correctly?
- Any errors or unexpected behaviour

**Output — write to `test-results/agent4-extraction.md`:**
```markdown
# Agent 4: Extraction Pipeline Report

## Summary
- Primary document: Mehta_Computers_financials_2024.xls
- Items extracted: N
- Extraction time: Xs
- Verification bypass: BLOCKED ✅ / NOT BLOCKED ❌

## Extracted Items (first 20)
| # | Description | Amount | Section |
|---|-------------|--------|---------|
...

## PDF Extraction (secondary test)
...

## Issues Found
...
```

---

### AGENT 5 — Classification Quality Judge

**Purpose:** Run the AI classification pipeline on the extracted data, then compare every result against the manually-done CMA. Find every error, categorize it, generate improvement rules. This is the most important agent.

**Prerequisites:** Agent 4 completed verification of `Mehta_Computers_financials_2024.xls`.

**Steps:**

1. **Trigger classification:**
   ```
   POST /api/classification/trigger
   Body: {"document_id": "{DOCUMENT_ID}", "industry": "Trading"}
   CRITICAL: Always pass industry="Trading" — the pipeline needs this context
   Expected: 200/202, task_id returned
   Poll until completed (max 300 seconds — AI calls take time)
   ```

2. **Collect all classification results:**
   ```
   GET /api/classification/results?document_id={DOCUMENT_ID}
   OR GET /api/cma-reports/{REPORT_ID}/classifications
   For each item record:
     - original description (from extraction)
     - assigned CMA field
     - which tier classified it (fuzzy/ai/doubt)
     - confidence score
     - CMA row number
   ```

3. **Load ground truth from CMA 15092025.xls:**
   Open `CMA 15092025.xls` → `INPUT SHEET`
   Read all non-empty rows in column D (FY2024 data — matches our test document)
   Build a dict: `{row_number: {"field_name": str, "value": float}}`
   This is the ground truth for FY2024 (column D = index 3 in 0-based).

4. **Compare AI output vs ground truth — for every classified item:**
   For each AI-classified item:
   - Find the corresponding row in the ground truth CMA INPUT SHEET
   - Check: did AI assign the correct CMA field (same row number)?
   - If mismatch: categorize the error using this taxonomy:

   **ERROR TAXONOMY:**
   ```
   TYPE A — Synonym Miss
     The item name in the financial statement is different from the reference
     mapping name but means the same thing.
     Example: "Staff Salaries" vs reference term "Salary and staff expenses"
     Fix needed: add synonym to fuzzy matcher or learned_mappings

   TYPE B — Industry Context Error
     Item classified correctly in general but wrong for THIS industry (Trading).
     Example: "Purchases" classified as "Raw Materials Consumed (Indigenous)"
     — technically same row in CMA, but conceptually wrong for a trading firm
     Fix needed: add industry-specific context to classification prompt

   TYPE C — Conditional Rule Override
     Item has a context-dependent rule in CMA classification sheet remarks.
     Example: "Lease Rent" → should be "Other Mfg Exp" if for factory use,
     but classified as "Rent, Rates and Taxes" without checking context
     Fix needed: extract all 11 remarks from classification sheet,
     add as conditional rules to AI classifier prompt

   TYPE D — Aggregation Error
     Multiple source items that should SUM into one CMA row were classified
     into different rows, or one item was split incorrectly.
     Fix needed: add pre-classification aggregation step

   TYPE E — Genuinely Novel / Out of Scope (CORRECT BEHAVIOUR)
     Item does not exist in the 387 reference items.
     System correctly sent it to doubt report.
     No fix needed — this is correct system behaviour.

   TYPE F — Ambiguous Conditional (CORRECT BEHAVIOUR)
     Item has a "depends on context" rule and system correctly doubted it.
     No fix needed — system working as designed.
   ```

5. **Compute metrics:**
   - Total items extracted for FY2024
   - % classified by Tier 1 (fuzzy) — target: >60%
   - % classified by Tier 2 (AI Haiku) — target: 20-30%
   - % sent to Tier 3 (doubt) — target: <15%
   - Overall accuracy vs ground truth (correct CMA field assigned %)
   - Per-field accuracy for the 10 key fields in Section 3 of this document

6. **Test the learning system:**
   Find one item that was misclassified (if any).
   Submit a correction:
   ```
   POST /api/classification/correct
   Body: {"item_id": "{item_id}", "correct_field": "{correct_cma_field}"}
   Expected: 200
   ```
   Then check learned_mappings table (via Supabase or API) — does the correction appear?
   This confirms the learning loop works.

7. **Generate improvement rules:**
   For each error found, write a concrete, actionable rule in this format:
   ```
   RULE [TYPE]: When source description contains "[pattern]",
   for industry "[industry]", classify as "[CMA field]" (row N)
   BECAUSE: [explanation from CMA classification sheet or business logic]
   PRIORITY: HIGH/MEDIUM/LOW based on frequency
   ```

**Output — write to `test-results/agent5-classification.md`:**
```markdown
# Agent 5: Classification Quality Report — Mehta Computers FY2024

## Executive Summary
- Total items extracted: N
- Tier 1 (fuzzy matched): N (X%)  avg confidence: 0.XX
- Tier 2 (AI Haiku):      N (X%)  avg confidence: 0.XX
- Tier 3 (doubt):         N (X%)
- Overall accuracy vs ground truth: X/N correct (X%)
- Learning system: WORKING / NOT WORKING

## Classification Results (Full Table)
| Source Description | AI Assigned Field | GT Row | GT Field | Match? | Error Type |
|--------------------|-------------------|--------|----------|--------|------------|
...

## Validation Against Known Values (FY2024 Column D)
| CMA Field | Expected Value | Extracted Value | Match? |
|-----------|---------------|-----------------|--------|
| Domestic Sales (R21) | 230.61052 | X.XX | ✅/❌ |
...

## Error Analysis

### Type A — Synonym Misses (N found)
...

### Type B — Industry Context Errors (N found)
...

### Type C — Conditional Rule Violations (N found)
...

### Type D — Aggregation Errors (N found)
...

### Type E — Correct Doubts (not errors) (N found)
...

### Type F — Correct Ambiguity Doubts (not errors) (N found)
...

## Improvement Rules Generated

### Rule 1 (HIGH priority)
...

### Rule 2 (HIGH priority)
...

## Learning System Test
...
```

---

### AGENT 6 — Excel Output Validator

**Purpose:** Verify the generated CMA .xlsm file is structurally correct, macros are preserved, and data lands in the right cells.

**Prerequisites:** Agent 5 completed. Approve all classified items (non-doubt) and resolve/assign doubt items.

**Steps:**

1. **Approve all classified items:**
   ```
   POST /api/classification/bulk-approve
   Body: {"document_id": "{DOCUMENT_ID}", "min_confidence": 0.0}
   OR approve individually via GET results + POST approve for each
   ```

2. **Resolve doubt items** (assign them to a CMA field):
   Get list of doubt items, assign each to the most reasonable CMA field based on the ground truth CMA.

3. **Trigger Excel generation:**
   ```
   POST /api/cma-reports/{REPORT_ID}/generate-excel
   Expected: 202, task_id returned
   Poll until completed (max 60 seconds)
   ```

4. **Download the generated file:**
   ```
   GET /api/cma-reports/{REPORT_ID}/download
   Expected: 200, file response (or signed URL)
   Save to: test-results/generated_cma.xlsm
   ```

5. **Validate file integrity:**
   ```python
   import os, zipfile
   filepath = "test-results/generated_cma.xlsm"

   # Check 1: file exists and is non-trivial size
   assert os.path.exists(filepath)
   assert os.path.getsize(filepath) > 50_000, "File too small — may be empty/corrupt"

   # Check 2: it's actually a zip (xlsx/xlsm are ZIP archives)
   assert zipfile.is_zipfile(filepath), "Not a valid ZIP/XLSX structure"

   # Check 3: VBA macros preserved — look for vbaProject.bin in ZIP
   with zipfile.ZipFile(filepath) as zf:
       names = zf.namelist()
       assert 'xl/vbaProject.bin' in names, "VBA macros STRIPPED — vbaProject.bin missing"
       vba_size = zf.getinfo('xl/vbaProject.bin').file_size
       assert vba_size > 5_000, f"VBA binary too small ({vba_size} bytes) — may be corrupt"
   ```

6. **Validate cell contents with openpyxl:**
   ```python
   from openpyxl import load_workbook
   wb = load_workbook(filepath, keep_vba=True)

   # Check INPUT SHEET exists
   assert 'INPUT SHEET' in wb.sheetnames

   sheet = wb['INPUT SHEET']

   # Check client name in correct cell
   # Row 7 in CMA = row index 6 (0-based), col B = index 1
   # openpyxl is 1-based: row 7, col 2
   client_cell = sheet.cell(row=7, column=2).value
   assert client_cell is not None, "Client name cell is empty"

   # Check year headers exist (row 8, cols B onward)
   year_b = sheet.cell(row=8, column=2).value
   assert year_b is not None, "Year header missing in row 8 col B"

   # Spot-check 3 known values for FY2024 (should be in the column corresponding to year 2024)
   # FY2024 is column D in ground truth = column index 4 in openpyxl
   # Find which column FY2024 is in (look at row 8)
   year_col = None
   for col in range(2, 14):
       val = sheet.cell(row=8, column=col).value
       if val and '2024' in str(val):
           year_col = col
           break

   if year_col:
       # Domestic Sales should be near row 22 (check ±2 rows)
       domestic_sales = sheet.cell(row=22, column=year_col).value
       # Expected: ~230.61 (from ground truth)
       # Allow 1% tolerance
       if domestic_sales:
           assert abs(float(domestic_sales) - 230.61052) < 2.5, \
               f"Domestic Sales value wrong: expected ~230.61, got {domestic_sales}"
   ```

7. **Check file is .xlsm not .xlsx:**
   Confirm saved filename ends with `.xlsm` (not `.xlsx`)

8. **Check TL Sheet exists:**
   ```python
   assert 'TL' in wb.sheetnames or 'TL Sheet' in wb.sheetnames
   ```

**Output — write to `test-results/agent6-excel.md`:**
```markdown
# Agent 6: Excel Output Validation Report

## Overall: PASS/FAIL

| Check | Result | Details |
|-------|--------|---------|
| File downloaded | PASS/FAIL | Size: N KB |
| File is .xlsm | PASS/FAIL | |
| ZIP structure valid | PASS/FAIL | |
| VBA macros present (vbaProject.bin) | PASS/FAIL | Size: N bytes |
| INPUT SHEET exists | PASS/FAIL | |
| Client name populated | PASS/FAIL | Value: "..." |
| Year headers present | PASS/FAIL | |
| Domestic Sales value correct | PASS/FAIL | Expected: 230.61, Got: X.XX |
| TL Sheet present | PASS/FAIL | |

## Cell-Level Validation (FY2024 column)
...

## Issues Found
...
```

---

### AGENT 7 — E2E Playwright User Journey

**Purpose:** Simulate a real CA using the app through a browser — 15 steps, screenshot every step.

**Prerequisites:** App running at localhost:3002. DISABLE_AUTH=true (mock admin active).

**Install Playwright if not installed:**
```bash
pip install playwright
playwright install chromium
```

**The 15-Step Journey:**

```python
from playwright.sync_api import sync_playwright
import os, time

SCREENSHOTS_DIR = "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/test-results/agent7-e2e"
BASE_URL = "http://localhost:3002"
BACKEND_URL = "http://localhost:8000"
RESULTS = []

def screenshot(page, step_num, step_name):
    path = f"{SCREENSHOTS_DIR}/step-{step_num:02d}-{step_name.replace(' ','-')}.png"
    page.screenshot(path=path)
    return path

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    # Step 1: Open the app
    page.goto(BASE_URL, wait_until="networkidle")
    screenshot(page, 1, "app-open")
    # Assert: page loaded (not blank, not error)

    # Step 2: Navigate to dashboard or login
    # If DISABLE_AUTH=true, app should show dashboard or redirect there
    page.wait_for_load_state("networkidle")
    screenshot(page, 2, "dashboard-or-login")
    # Assert: URL is /dashboard or /login or /clients

    # Step 3: Navigate to Clients page
    page.goto(f"{BASE_URL}/clients", wait_until="networkidle")
    screenshot(page, 3, "clients-page")
    # Assert: page title or heading contains "Client"

    # Step 4: Create a new client
    # Look for "New Client" or "Add Client" button
    new_btn = page.locator("text=New Client, text=Add Client, button:has-text('Client')").first
    new_btn.click()
    page.wait_for_load_state("networkidle")
    screenshot(page, 4, "new-client-form")

    # Fill the form
    page.fill("input[name='name'], input[placeholder*='name' i]", "E2E Test Client")
    page.select_option("select[name='industry']", "Trading") if page.locator("select[name='industry']").count() > 0 else None
    screenshot(page, 5, "form-filled")

    # Submit
    page.click("button[type='submit'], button:has-text('Save'), button:has-text('Create')")
    page.wait_for_load_state("networkidle")
    screenshot(page, 6, "client-created")
    # Assert: no error toast, URL changed (client was saved)
    client_url = page.url
    # Extract client ID from URL if possible

    # Step 7: Navigate to upload page for this client
    # Look for "Upload" tab or button on client detail page
    upload_link = page.locator("text=Upload, a:has-text('Upload'), button:has-text('Upload')").first
    if upload_link.count() > 0:
        upload_link.click()
    else:
        # Navigate directly
        page.goto(f"{BASE_URL}/clients/{client_url.split('/')[-1]}/upload", wait_until="networkidle")
    page.wait_for_load_state("networkidle")
    screenshot(page, 7, "upload-page")

    # Step 8: Upload a document (use the 2024 Excel file)
    doc_path = "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/DOCS/Excel_project/Mehta computer/Mehta_Computers_financials_2024.xls"
    # react-dropzone uses a hidden file input
    file_input = page.locator("input[type='file']")
    if file_input.count() > 0:
        file_input.set_input_files(doc_path)
    page.wait_for_load_state("networkidle")
    screenshot(page, 8, "file-selected")

    # Click upload/submit if needed
    upload_btn = page.locator("button:has-text('Upload'), button[type='submit']").first
    if upload_btn.count() > 0:
        upload_btn.click()
    page.wait_for_load_state("networkidle")
    screenshot(page, 9, "upload-complete")

    # Step 10: Wait for extraction progress
    # Look for progress bar or "extracting" status
    time.sleep(5)  # give extraction a moment to start
    screenshot(page, 10, "extraction-progress")

    # Step 11: Open verification screen
    verify_link = page.locator("text=Verify, a:has-text('Verify'), button:has-text('Verify')").first
    if verify_link.count() > 0:
        verify_link.click()
        page.wait_for_load_state("networkidle")
    screenshot(page, 11, "verification-screen")
    # Assert: table of extracted items visible

    # Step 12: Confirm verification
    confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('Verify All'), button:has-text('Approve')").first
    if confirm_btn.count() > 0:
        confirm_btn.click()
        page.wait_for_load_state("networkidle")
    screenshot(page, 12, "verification-confirmed")

    # Step 13: Navigate to classification review
    review_link = page.locator("text=Review, text=Classify, a:has-text('Review')").first
    if review_link.count() > 0:
        review_link.click()
        page.wait_for_load_state("networkidle")
    screenshot(page, 13, "classification-review")

    # Step 14: Generate Excel
    generate_btn = page.locator("button:has-text('Generate'), button:has-text('Download CMA')").first
    if generate_btn.count() > 0:
        with page.expect_download(timeout=30000) as download_info:
            generate_btn.click()
        download = download_info.value
        screenshot(page, 14, "excel-downloaded")
        # Assert: downloaded file ends with .xlsm
        assert download.suggested_filename.endswith('.xlsm') or download.suggested_filename.endswith('.xls')
    else:
        screenshot(page, 14, "generate-button-not-found")

    # Step 15: Final state
    screenshot(page, 15, "final-state")
    browser.close()
```

Record pass/fail for each step. If a step fails (element not found, unexpected error), note what was visible on screen and continue if possible — don't abort the entire journey for one missing element.

**Output — write to `test-results/agent7-e2e/log.md`:**
```markdown
# Agent 7: E2E Playwright Journey Report

## Overall: PASS (N/15 steps completed)

| Step | Description | Result | Screenshot |
|------|-------------|--------|------------|
| 1 | Open app | PASS | step-01-app-open.png |
| 2 | Dashboard loads | PASS | step-02-dashboard-or-login.png |
...

## Failures and Observations
...

## Screenshots
All screenshots saved to: test-results/agent7-e2e/
```

---

### AGENT 8 — Chaos Monkey (Edge Cases)

**Purpose:** Try to break the app with bad inputs, unexpected sequences, and edge cases.

**Steps — run each, record what happens:**

1. **Blank Excel upload:**
   Create a completely empty .xlsx file (just open openpyxl, save immediately).
   Upload it. Trigger extraction.
   Expected: graceful error (not 500), extraction status="failed" with a message.

2. **Tiny file disguised as PDF:**
   Create a 10-byte text file named `fake.pdf`.
   Upload it.
   Expected: either 400 rejection OR extraction fails gracefully.

3. **Client name with special characters:**
   `POST /api/clients` with name: `"Sharma & Sons (Pvt.) Ltd."`
   Then retrieve it.
   Expected: name stored and retrieved exactly as-is (& and . not corrupted).

4. **Very long client name (300 chars):**
   Create client with name = "A" × 300.
   Expected: either 422 (too long) or truncated — NOT a 500 server error.

5. **Classify before verification (duplicate test from Agent 4):**
   Upload a new document, trigger extraction, then immediately try to classify.
   Expected: 400 or 403 — "verification required first".
   This MUST be blocked.

6. **Generate Excel with unresolved doubts:**
   Have at least one doubt item, try to generate Excel.
   Expected: blocked with message about unresolved doubts.
   (If app allows it anyway, note as MEDIUM severity issue.)

7. **Same line item appearing 3 times:**
   Manually edit an extracted item via the API to create duplicates (or find if the real document has this case).
   Then classify.
   Expected: amounts summed into one CMA row, not three separate entries.

8. **Concurrent extraction of same document:**
   Trigger extraction twice within 1 second for the same document_id.
   Expected: second call either rejected (409 conflict) or idempotent (returns same task).
   NOT expected: two parallel extraction jobs running simultaneously.

9. **Very large amount (test number formatting):**
   If possible, edit an extracted item to have amount = 99999999.99
   Verify it stores and retrieves correctly (no float precision errors, no overflow).

10. **Non-existent financial year:**
    `POST /api/documents/upload` with `financial_year: "1850"`
    Expected: 422 validation error, not 500.

**Output — write to `test-results/agent8-chaos.md`:**
```markdown
# Agent 8: Chaos Monkey Report

## Summary: N/10 edge cases handled correctly

| Test | Input | Expected | Got | Result | Severity if Failed |
|------|-------|----------|-----|--------|--------------------|
| Blank Excel | empty.xlsx | graceful error | ... | PASS/FAIL | HIGH |
...

## Unexpected Behaviours Found
...
```

---

## 7. FINAL REPORT ASSEMBLY (AGENT 0 — LAST STEP)

After all agents complete, assemble `test-results/TEST_REPORT.md`:

```markdown
# CMA Automation V1 — Test Report
**Generated:** [timestamp]
**Company tested:** Mehta Computers
**Industry:** Trading
**Documents tested:** 7 financial files (FY2022–FY2025)

---

## Overall Score: N/N agents passed

| Agent | Purpose | Result | Key Metric |
|-------|---------|--------|------------|
| 0.5 | Document Intelligence | PASS | 7 docs identified |
| 1 | Infrastructure | PASS | All 10 checks green |
| 2 | Security | PASS/FAIL (N issues) | Critical: N, High: N |
| 3 | API Contract | PASS | N/M endpoints passed |
| 4 | Extraction | PASS | N items extracted in Xs |
| 5 | Classification Quality | PASS | X% accuracy, N rules generated |
| 6 | Excel Validation | PASS | VBA preserved, cells correct |
| 7 | E2E Journey | PASS | N/15 steps completed |
| 8 | Chaos | PASS | N/10 edge cases handled |

---

## Classification Pipeline Report (Most Important)
[Copy key metrics from agent5-classification.md]

## Improvement Rules (Generated by Agent 5)
[Copy all generated rules from agent5-classification.md]
These should be added to the classification pipeline to improve accuracy.

## Bugs Found

### CRITICAL (fix before any real use)
[From agents 2, 3, 4, 5, 6, 7, 8]

### HIGH
### MEDIUM
### LOW

## Excel Output Validation
[Key results from agent6-excel.md]

## E2E Screenshots
All screenshots: test-results/agent7-e2e/

---

## Recommended Next Actions
1. [Most urgent fix]
2. [Second priority]
3. [Classification rule additions from Agent 5]
```

---

## 8. WHAT TO DO WHEN THINGS GO WRONG

| Situation | Action |
|-----------|--------|
| Agent 1 gate fails (infrastructure down) | STOP. Tell user exactly which service is down and how to restart it. |
| Docker container not running | Tell user: `docker compose up` |
| Backend returns 502/503 | Tell user: `docker compose restart backend` |
| Extraction task stuck (>120s) | Check ARQ worker: `docker logs cmaproject-2-backend-1 --tail 50` |
| Playwright cannot find element | Take screenshot of current page state. Note what's visible. Continue with next step. |
| Agent 5 cannot compare (ground truth unreadable) | Use xlrd to read `CMA 15092025.xls`. If xlrd fails, use openpyxl with read_only=True. |
| File not found in zip | Extract zip first: `import zipfile; zipfile.ZipFile(path).extractall(dest)` |
| 401 errors with DISABLE_AUTH=true | Check .env file has `DISABLE_AUTH=true` (not `DISABLE_AUTH=True`) and backend was restarted after change |
| Agent 2 cannot restore DISABLE_AUTH | ALWAYS restore DISABLE_AUTH=true before ending Agent 2. Check .env manually. |

---

## 9. QUICK REFERENCE — KEY VALUES

```
Backend URL:         http://localhost:8000
Frontend URL:        http://localhost:3002
Supabase project:    sjdzmkqfsehfpptxoxca
Company name:        Mehta Computers
Industry:            Trading
CMA ground truth:    DOCS/Excel_project/Mehta computer/CMA 15092025.xls
Reference mappings:  DOCS/CMA classification.xls (387 items)
Test user email:     admin@cma.test
Test user password:  CmaAdmin@2024
Results folder:      test-results/
```

---

*End of master execution instructions. Start with Agent 0.5 and work through the tiers.*
*If you are reading this, do not re-plan. Execute.*
