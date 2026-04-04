# Window 1: BCIPL Full E2E App Test with Playwright

> **PASTE THIS INTO A FRESH CLAUDE CODE WINDOW (Opus 4.6, High Effort)**
> Read the ENTIRE prompt before doing anything.

---

## YOUR ROLE

You are testing the CMA Automation System end-to-end through the real browser UI using Playwright MCP tools. You will walk through every feature — login, client creation, document upload, extraction, verification, classification, intelligent doubt resolution, Excel generation, download, and logout.

**Two critical behaviors:**
1. **FIX-IF-BROKEN**: If any step fails, you diagnose, fix the code, rebuild containers, and retry. If still broken after a fix, apply `/autoresearch:debug` (max 3 iterations). If still broken after that, document the bug and continue.
2. **INTELLIGENT DOUBT RESOLUTION**: When you encounter classification doubts, you READ each line item's description, amount, and context, then use CA (Chartered Accountant) domain knowledge to pick the correct CMA field. You do NOT bulk-approve blindly.

---

## CONSTRAINTS — READ THESE FIRST

1. **NEVER** create unbounded loops. Max 30 polls for any wait. Max 3 retries per failed step.
2. Take a screenshot after EVERY major step. Save to `DOCS/test-results/bcipl/run-2026-04-04/`.
3. If something fails: screenshot → diagnose → fix → rebuild → retry. If still broken: `/autoresearch:debug`.
4. Total test budget: 90 minutes wall-clock. If exceeded, stop and report.
5. Use Playwright MCP tools (browser_navigate, browser_click, browser_fill_form, browser_snapshot, browser_take_screenshot, browser_file_upload, browser_wait_for).
6. Record cost: check OpenRouter balance before and after.

---

## SYSTEM STATE

```
Backend:      http://localhost:8000     (FastAPI)
Frontend:     http://localhost:3002     (Next.js)
Worker:       ARQ task queue            (async extraction/classification/generation)
Redis:        localhost:6379
Auth:         REAL Supabase Auth (DISABLE_AUTH=false)
Supabase:     Project sjdzmkqfsehfpptxoxca (ap-southeast-2)
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
```

Docker services are already running. Verify with `docker compose ps` before starting.

---

## AUTH CREDENTIALS

```
Email:    ashutosh@cma-test.in
Password: CmaTest@2026
Role:     admin
User ID:  b6352de6-5526-4c3c-9344-72bfd5765b87
```

---

## TEST DATA

| File | Path | FY | Source Unit |
|------|------|----|-------------|
| FY2021 | `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls` | 2021 | **rupees** |
| FY2022 | `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls` | 2022 | **lakhs** |
| FY2023 | `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls` | 2023 | **rupees** |

**CRITICAL**: FY2022 is in LAKHS, not rupees. Set `source_unit` correctly during upload.

**CMA Output Unit**: **crores** (ground truth confirmed: B13 = `'In crs'`)

---

## STEP 0: PRE-FLIGHT

```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
docker compose ps                    # All 5 services running?
curl http://localhost:8000/health     # {"status":"ok","db":"ok"}?
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002  # 200?
```

Create output directory:
```bash
mkdir -p "DOCS/test-results/bcipl/run-2026-04-04"
```

Record OpenRouter balance:
```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $(grep OPENROUTER_API_KEY .env | cut -d= -f2)" \
  | python -c "import json,sys; d=json.load(sys.stdin); print(f'Balance: {d}')"
```

Save as `preflight.json`. **STOP if any check fails.**

---

## STEP 1: LOGIN

1. Navigate to `http://localhost:3002/login`
2. Fill email: `ashutosh@cma-test.in`
3. Fill password: `CmaTest@2026`
4. Click "Sign in"
5. Wait for redirect to `/clients`
6. **Screenshot**: `step-01-login-success.png`

**Verify**: URL contains `/clients`, no error toast

**IF BROKEN**: Check browser console for Supabase auth errors. Common issues:
- CORS: check backend CORS config in `backend/app/main.py`
- Supabase URL mismatch: check `frontend/.env` has correct `NEXT_PUBLIC_SUPABASE_URL`
- User not found: verify user exists via Supabase MCP `execute_sql`

---

## STEP 2: CREATE CLIENT

1. Navigate to `/clients/new`
2. Fill "Client Name": `BCIPL`
3. Select Industry: `Manufacturing`
4. Click "Create" / "Save"
5. Wait for redirect to `/clients/{client_id}`
6. **Screenshot**: `step-02-client-created.png`

**Verify**: "BCIPL" visible on page, industry shows "Manufacturing"
**Save**: `client_id` from the URL

---

## STEP 3-5: UPLOAD 3 DOCUMENTS

Navigate to the upload page from the client detail (click "Upload" link → `/clients/{client_id}/upload`).

**Screenshot**: `step-03-upload-page.png`

For each document:

### Document 1: FY2021
- File: `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls`
- Document Type: `Combined Financial Statement`
- Financial Year: `2021`
- Nature: `Audited`
- Source Unit: `Rupees`
- **Screenshot**: `step-04-upload-fy2021.png`

### Document 2: FY2022
- File: `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls`
- Document Type: `Combined Financial Statement`
- Financial Year: `2022`
- Nature: `Audited`
- Source Unit: **`Lakhs`** (NOT rupees!)
- **Screenshot**: `step-05-upload-fy2022.png`

### Document 3: FY2023
- File: `C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls`
- Document Type: `Combined Financial Statement`
- Financial Year: `2023`
- Nature: `Audited`
- Source Unit: `Rupees`
- **Screenshot**: `step-06-upload-fy2023.png`

**Screenshot after all 3**: `step-07-all-docs-uploaded.png`
**Verify**: All 3 documents visible in document list with correct metadata

**IF FILE UPLOAD FAILS IN BROWSER**: Use API fallback:
```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "client_id={CLIENT_ID}" \
  -F "document_type=combined_financial_statement" \
  -F "financial_year=2021" \
  -F "nature=audited" \
  -F "source_unit=rupees" \
  -F "file=@C:/Users/ASHUTOSH/OneDrive/Desktop/FInancial Analysis/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls"
```
Get token first: login via API `POST /api/auth/login` with `{"email":"ashutosh@cma-test.in","password":"CmaTest@2026"}` → extract `access_token` from response.

---

## STEP 6: EXTRACT ALL 3 DOCUMENTS

For each document, navigate to the verify page or trigger extraction.

The extraction flow per document:
1. Navigate to `/cma/{document_id}/verify` (the verify page for that document)
2. If it shows sheet selection → accept defaults → click "Extract"
3. If it shows "Extract" button → click it
4. Wait for extraction to complete (progress indicator)
5. **Max 30 polls, 5 seconds each** (2.5 minutes per doc)

**Screenshots**:
- `step-08-doc1-extracting.png`
- `step-09-doc2-extracting.png`
- `step-10-doc3-extracting.png`

**Verify per document**:
- Extraction completes (status → "extracted")
- Item count: 30-200 items (if >300 → sheet filtering bug)
- Key items visible: Revenue, Raw Materials, Share Capital

**Record**: Item count per document in the test report.

**IF EXTRACTION FAILS**: Check worker logs:
```bash
docker compose logs --tail=50 worker
```
Common issues: OpenRouter API key invalid, model not available, file format not supported.

---

## STEP 7: VERIFY ALL 3 DOCUMENTS

For each document on the verify page:
1. Review the extracted line items table
2. Check that descriptions and amounts look reasonable
3. Click "Verify" / "Confirm Verification" button
4. Status should change to "verified"

**Screenshots**:
- `step-11-doc1-verified.png`
- `step-12-doc2-verified.png`
- `step-13-doc3-verified.png`

---

## STEP 8: CREATE CMA REPORT

1. Navigate back to client detail: `/clients/{client_id}`
2. Click "New Report" or navigate to `/clients/{client_id}/cma/new`
3. Fill:
   - Report Title: `BCIPL CMA FY2021-FY2023`
   - CMA Output Unit: **Crores**
   - Select all 3 documents
4. Click "Create Report"
5. Wait for redirect to `/cma/{report_id}`
6. **Screenshot**: `step-14-report-created.png`

**Save**: `report_id` from the URL

---

## STEP 9: CLASSIFICATION

Classification runs automatically after report creation (triggered by the worker).

1. On the CMA report page (`/cma/{report_id}`), watch the confidence dashboard
2. Poll/refresh every 15-20 seconds
3. **Max 40 refreshes** (10-12 minutes)
4. Classification is complete when all items are classified

**Screenshot**: `step-15-classification-complete.png`

**Record**: Confidence breakdown:
```
Total items: XX
High confidence (>=0.85): XX
Medium confidence (0.6-0.85): XX
Needs review: XX
Doubts: XX
```

**IF CLASSIFICATION IS SLOW (>10 min)**:
```bash
docker compose logs --tail=50 worker
```
Check for rate limit errors or API failures.

---

## STEP 10: INTELLIGENT DOUBT RESOLUTION (THE KEY STEP)

Navigate to the review page: `/cma/{report_id}/review` or `/cma/{report_id}/doubts`

**Screenshot**: `step-16-doubts-page.png`

### For EACH doubt item:

1. **Read** the line item: description, amount, section (P&L or BS), document (which FY)
2. **Read** the AI's `doubt_reason`, `ai_best_guess`, and `alternative_fields`
3. **Apply CA domain knowledge** to determine the correct CMA field:

   **P&L Classification Guide:**
   - Revenue/Sales/Turnover/Income from Operations → Row 22 (Domestic) or 23 (Export)
   - Raw Materials/Materials Consumed → Row 41 (Imported) or 42 (Indigenous)
   - Stores/Spares/Consumables → Row 43 (Imported) or 44 (Indigenous)
   - Wages/Employee Benefits (manufacturing) → Row 45
   - Job Work/Processing Charges → Row 46
   - Freight/Transportation → Row 47
   - Power/Electricity/Fuel → Row 48
   - Repairs (factory/plant) → Row 50
   - Salary/Staff (office/admin) → Row 67
   - Rent/Rates/Taxes → Row 68
   - Bad Debts → Row 69
   - Commission/Discount/Brokerage/Selling → Row 70
   - Other Admin Expenses → Row 71
   - Audit Fee/Director Remuneration → Row 73
   - Interest on Term Loan → Row 83
   - Interest on Working Capital/CC/OD → Row 84
   - Bank Charges → Row 85
   - Income Tax/Tax Provision → Row 99
   - Deferred Tax → Row 100 or 101
   - Depreciation → Row 56 (manufacturing) or 63 (CMA general)

   **Balance Sheet Classification Guide:**
   - Share Capital/Paid Up → Row 116
   - Reserves (General/P&L/Share Premium) → Rows 121-125
   - Working Capital Loans/CC/OD → Row 131
   - Term Loan (< 1 year) → Row 136; (> 1 year) → Row 137
   - Unsecured Loans (Quasi Equity/Directors) → Row 152
   - Gross Block/Fixed Assets → Row 162
   - Accumulated Depreciation → Row 163
   - Raw Material Inventory → Row 194
   - Finished Goods Inventory → Row 201
   - Trade Receivables/Debtors (domestic) → Row 206
   - Cash → Row 212; Bank Balance → Row 213
   - Trade Payables/Creditors → Row 242
   - Provisions for Tax → Row 244

4. **Resolve** via the UI:
   - If the AI's best guess is correct → click "Approve"
   - If the AI's best guess is wrong → select the correct CMA field from the dropdown → click "Save" / "Correct"

5. **Document** your reasoning in a JSON log:
```json
{
  "line_item": "Employee Benefits Expense",
  "amount": 1253000,
  "doubt_reason": "Could be Wages (manufacturing) or Salary (admin)",
  "ai_best_guess": "Wages",
  "my_decision": "Wages",
  "reasoning": "BCIPL is manufacturing — majority of employees are factory workers. Employee Benefits Expense in Indian financial statements typically maps to Wages (Row 45) for manufacturing companies.",
  "action": "approved"
}
```

Save all doubt resolutions to `DOCS/test-results/bcipl/run-2026-04-04/doubt-resolutions.json`.

**Screenshot**: `step-17-doubts-resolved.png`

### After resolving ALL doubts:
- Navigate to review page and do a final bulk approve if any remaining items need it
- **Screenshot**: `step-18-all-approved.png`
- Verify: confidence dashboard shows 0 "needs review"

---

## STEP 11: GENERATE EXCEL

1. Navigate to `/cma/{report_id}` or `/cma/{report_id}/generate`
2. Click "Generate Excel" button
3. Wait for generation to complete (polls automatically)
4. **Max 30 polls, 10 seconds each** (5 minutes)
5. **Screenshot**: `step-19-generation-complete.png`

**Verify**: Status = "complete", download button visible

**IF GENERATION FAILS**:
```bash
docker compose logs --tail=50 worker
```
Common issues: template file not found, openpyxl errors, missing classifications.

---

## STEP 12: DOWNLOAD EXCEL

1. Click "Download" button on the generate/report page
2. The browser downloads a `.xlsm` file
3. Save/move it to: `DOCS/test-results/bcipl/run-2026-04-04/BCIPL_generated_CMA.xlsm`

**If browser download doesn't work**, use API:
```bash
# Get download URL
curl -s http://localhost:8000/api/cma-reports/{REPORT_ID}/download \
  -H "Authorization: Bearer $TOKEN"
# Returns {"signed_url": "...", "expires_in": 60}

# Download the file
curl -L "{SIGNED_URL}" -o "DOCS/test-results/bcipl/run-2026-04-04/BCIPL_generated_CMA.xlsm"
```

4. Verify file:
```bash
ls -la "DOCS/test-results/bcipl/run-2026-04-04/BCIPL_generated_CMA.xlsm"
# Must be > 50KB
```

**Screenshot**: `step-20-file-downloaded.png`

---

## STEP 13: LOGOUT

1. Find and click logout button (header or user menu dropdown)
2. Wait for redirect to `/login`
3. **Screenshot**: `step-21-logged-out.png`

**Verify**: URL = `/login`, protected routes no longer accessible

---

## STEP 14: RECORD FINAL COST

```bash
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $(grep OPENROUTER_API_KEY .env | cut -d= -f2)" \
  | python -c "import json,sys; d=json.load(sys.stdin); print(f'Balance: {d}')"
```

Calculate: `cost = pre_balance - post_balance`

---

## STEP 15: COMPILE E2E TEST REPORT

Save to `DOCS/test-results/bcipl/run-2026-04-04/test-report-e2e.md`:

```markdown
# BCIPL E2E Browser Test Report
**Date:** 2026-04-04
**Tester:** Claude Opus 4.6 (automated)
**Auth:** Real Supabase Auth (ashutosh@cma-test.in)

## Pre-flight
- Docker: [status]
- Backend health: [status]
- Frontend: [status]
- OpenRouter balance before: $X.XX

## Results Per Step
| Step | Feature | Result | Time | Notes |
|------|---------|--------|------|-------|
| 1 | Login | pass/fail | | |
| 2 | Create Client | pass/fail | | |
| ... | ... | ... | | |
| 13 | Logout | pass/fail | | |

## Extraction Summary
| Doc | FY | Items | Source Unit | Status |
|-----|----|-------|-------------|--------|

## Classification Summary
| Metric | Value |
|--------|-------|
| Total | |
| High confidence | |
| Doubts | |
| Doubts resolved by Opus | |

## Doubt Resolutions
[Include the full doubt-resolutions.json content here as a table]

## Bugs Found & Fixed
| Bug | Where | Fix | Retry Result |
|-----|-------|-----|--------------|

## Cost
- OpenRouter before: $X.XX
- OpenRouter after: $X.XX
- Total cost: $X.XX
- API calls (from worker logs): XX

## Screenshots
[List all screenshots taken]

## Overall Verdict
**PASS / PARTIAL PASS / FAIL**
[Summary paragraph]

## File for Window 2
Generated Excel saved at:
`DOCS/test-results/bcipl/run-2026-04-04/BCIPL_generated_CMA.xlsm`
```

---

## FIX-IF-BROKEN REFERENCE

### Quick diagnosis commands
```bash
# Backend logs
docker compose logs --tail=50 backend

# Worker logs (extraction/classification/generation)
docker compose logs --tail=50 worker

# Frontend logs
docker compose logs --tail=50 frontend

# Redis check
docker compose exec redis redis-cli ping

# Rebuild and restart
docker compose up -d --build backend worker
```

### Common fixes
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| 401 on all API calls | Auth token expired | Re-login, get fresh token |
| 404 on document endpoints | Wrong API path | Check route prefixes in routers |
| Extraction stuck | Worker crashed | `docker compose restart worker` |
| "OpenRouter error" in logs | API key or balance | Check `.env` OPENROUTER_API_KEY |
| CORS error in browser | Origin not allowed | Add origin to `backend/app/main.py` cors_origins |
| Upload fails | File path wrong | Verify file exists at exact path |
| Classification timeout | Rate limiting | Wait, check OpenRouter status |
| Generation fails | Template missing | Check CMA.xlsm mount in docker-compose.yml |

### When to use /autoresearch:debug
If a fix attempt fails and you can't diagnose the root cause after reading logs + code:
1. Invoke `/autoresearch:debug`
2. Describe the symptom, what you tried, what logs show
3. Let it run the scientific-method loop (max 3 iterations)
4. If it finds the fix, apply it and continue
5. If 3 iterations fail, document as unresolved bug and skip the step
