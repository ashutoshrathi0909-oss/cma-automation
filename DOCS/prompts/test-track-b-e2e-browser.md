# Test Track B — Full App E2E Browser Test

## Your Role
You are a testing agent. Your ONLY job is to validate the complete CMA workflow works end-to-end through the browser with the new scoped classification engine. You test the INTEGRATION, not the accuracy (Track A handles accuracy). You do NOT fix bugs — you report them.

## Load Required Skill
Use `superpowers:e2e-testing` or Playwright MCP tools for browser interaction. Use `superpowers:verification-before-completion` before claiming results.

## Important Notes (Post-Integration Updates)

> **Model change:** DeepSeek R1 has been replaced with **DeepSeek V3** (`deepseek/deepseek-chat`). V3 is a fast generation model. Classification should take **minutes, not hours**.
>
> **Bugs found and fixed during integration (4):**
> 1. **`classify_sync` crash** — `asyncio.get_event_loop()` crashed in ARQ worker threads. Fixed to use `asyncio.new_event_loop()`.
> 2. **GET /api/documents/{id} missing** — Was returning 405 (only DELETE existed). Proper GET endpoint added.
> 3. **Row offset in canonical_labels.json** — All `sheet_row` values were off by -1. Bumped +1 to match CMA Excel template.
> 4. **Ground truth path** — `parents[4]` was wrong for Docker layout. Changed to `parents[3]`.
> 5. **pipeline.py hardcoded method** — Lines 191/217 had `"ai_haiku"` instead of `ai_result.classification_method`.
>
> All 5 fixes are applied. If you see any of these issues recurring, it means the fix was lost — report immediately.

## Pre-Flight Check

### Verify Docker is running
```bash
docker compose ps
```
All 4 services must be "Up". If not:
```bash
docker compose up -d
```

### Verify frontend is accessible
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002
```
Expected: 200 (or 302 redirect to login). If connection refused → wait 30s and retry once.

### Verify backend health
```bash
curl -s http://localhost:8000/health
```
Expected: JSON response with status "ok" or "degraded".

---

## The E2E Test — Step by Step

**CRITICAL: You MUST create a NEW client and go through the FULL workflow from scratch. Do NOT reuse existing clients, documents, or data. The purpose is to validate the entire pipeline end-to-end.**

You will walk through the COMPLETE CMA workflow in the browser. At each step, verify the expected behavior and screenshot any issues.

### Step 1: Login
- Navigate to `http://localhost:3002/login`
- The app may have a dev bypass (check if login auto-fills or has a dev mode)
- If real credentials needed: check `.env` for `E2E_ADMIN_EMAIL` and `E2E_ADMIN_PASSWORD`
- If no credentials found: try `admin@test.local` / `testpassword`
- Expected: Redirected to dashboard after login

### Step 2: Create a Test Client
- Navigate to Clients → New Client (or `/clients/new`)
- Fill in:
  - Client Name: `Scoped v2 E2E Test`
  - Industry Type: `Manufacturing`
- Click Create/Save
- **IMPORTANT:** You MUST create a NEW client. Do not reuse any existing client.
- Expected: Redirected to client detail page, client name visible

### Step 3: Upload a Document
- From client detail page, click Upload (or navigate to upload page)
- Upload a test document. Look for test files in these locations:
  - `DOCS/Financials/BCIPL/` — real financial PDFs/Excel
  - `e2e/fixtures/` — existing test fixtures
  - Any `.xlsx` or `.pdf` in the DOCS folder
- Select document type: `profit_and_loss` or `balance_sheet`
- Select financial year if prompted
- Click Upload
- Expected: Upload succeeds, document appears in list with status "pending"

### Step 4: Wait for Extraction
- Extraction should start automatically or be triggered via button
- Watch for status to change: pending → processing → extracted
- This may take 30-60 seconds for PDF, instant for Excel
- Check worker logs if it seems stuck:
  ```bash
  docker compose logs worker --tail=30
  ```
- Expected: Status reaches "extracted"

### Step 5: Verify Extraction
- Navigate to the Verify page for this CMA report
- Review the extracted line items — they should show:
  - Description/source text
  - Amount
  - Section
- Click "Mark as Verified" (or verify individual items then confirm)
- Expected: Extraction status changes to "verified"

### Step 6: Trigger Classification (THE KEY TEST)
- After verification, classification should start automatically
- If not automatic, look for a "Classify" button and click it
- **Classification should complete in minutes, not hours** (DeepSeek V3 is ~1.9s per item)
- **Immediately check worker logs:**
  ```bash
  docker compose logs worker -f --tail=5
  ```
- Expected logs should show:
  - `run_classification started for document_id=...`
  - Evidence of scoped classification (section routing, model calls)
  - DeepSeek V3 (`deepseek/deepseek-chat`) and/or Gemini Flash references
  - Agreement/debate decisions
  - Classification completing
- **Expected worker log method patterns:** `scoped_agree`, `scoped_debate`, `scoped_single_deepseek`, `scoped_single_gemini`
- If you see `ai_haiku` in the logs, the pipeline.py fix may have been lost — report it
- If you see `deepseek/deepseek-r1` instead of `deepseek/deepseek-chat`, the model swap was not applied — report it

### Step 7: Verify Classification Results in UI
- Wait for classification to complete (status should update in browser)
- Navigate to the Review page
- Expected:
  - Line items listed with CMA field assignments
  - Confidence scores visible
  - Classification method should show `scoped_agree`, `scoped_debate`, `scoped_single_deepseek`, or `scoped_single_gemini` — NOT `ai_haiku`
  - Some items marked as doubt (is_doubt=true)

### Step 8: Check the Doubt Report
- Navigate to the Doubts page
- Expected:
  - Doubt items listed with reasoning
  - Should be a small percentage of total (< 20% for this test)
  - Each doubt should have reasoning from the debate

### Step 9: Approve Some Classifications
- On the Review page, try:
  - Approve a high-confidence item
  - Correct a doubt item (change its CMA field)
  - Bulk approve if the button exists
- Expected: Status updates work, corrections save

### Step 10: Generate Excel (CRITICAL)
- Navigate to the Generate page
- Click Generate Excel (may need minimum approved items)
- Wait for generation to complete
- Download the file
- **This step MUST succeed.** The E2E test is not complete until Excel generation works.
- Expected: .xlsm file downloads

### Step 11: Verify Excel (CRITICAL)
- Open downloaded file (or check its properties)
- Verify:
  - File is .xlsm (not .xlsx) — macros preserved
  - INPUT SHEET has data filled in
  - Values appear in correct rows (row offset was fixed — verify data lands in the right cells)
- If you can't open Excel, at minimum verify the file exists and is > 10KB
- **This step MUST succeed.** A downloaded empty or corrupt Excel means the pipeline is broken.

---

## What To Log

At each step, record:
1. Did it work? (PASS / FAIL / PARTIAL)
2. Any errors in browser console or worker logs
3. Screenshots of any failures
4. Time taken for classification specifically

## Report Format

Produce this summary:

```
## E2E Test Results — Scoped Classification v2 (DeepSeek V3 + Gemini Flash)

### Environment
- Docker: [all services up? Y/N]
- Frontend: [accessible? Y/N]
- Backend: [healthy? Y/N]

### Workflow Steps
| Step | Description | Result | Notes |
|------|-------------|--------|-------|
| 1 | Login | PASS/FAIL | |
| 2 | Create client (NEW) | PASS/FAIL | Must be fresh client |
| 3 | Upload document | PASS/FAIL | |
| 4 | Extraction | PASS/FAIL | |
| 5 | Verification | PASS/FAIL | |
| 6 | Classification | PASS/FAIL | [this is the critical one] |
| 7 | Review UI | PASS/FAIL | |
| 8 | Doubt report | PASS/FAIL | |
| 9 | Approve/correct | PASS/FAIL | |
| 10 | Excel generation | PASS/FAIL | [CRITICAL — must generate] |
| 11 | Excel verification | PASS/FAIL | [CRITICAL — must have data] |

### Classification Details (from worker logs)
- Classification method: [scoped_agree / scoped_debate / scoped_single_* / unknown]
- Models used: [DeepSeek V3 + Gemini Flash / unknown]
- Items classified: ??
- Items flagged as doubt: ??
- Agreement rate: ?? (if visible in logs)
- Total classification time: ??s (should be minutes, not hours)
- Any errors: [list]

### Blocking Issues
[List any step that FAILed and would block production use]

### Non-Blocking Issues
[List any step that had warnings or cosmetic issues]
```

Save report to `DOCS/test-results/scoped-v2/E2E_REPORT.md`

---

## Constraints
- DO NOT modify any source code — test only, report issues
- DO NOT fix bugs you find — document them clearly
- DO NOT delete or modify existing data in the database
- **MUST create a NEW test client** — do not reuse existing clients or data
- **MUST go through ALL 11 steps** — Steps 10 and 11 (Excel generation + verification) are especially critical
- If classification fails completely, capture the full error from worker logs
- If the frontend is broken, still check if the backend API works via curl
- Classification should take minutes (DeepSeek V3 is fast) — if it takes more than 30 minutes for a single document, something is wrong
