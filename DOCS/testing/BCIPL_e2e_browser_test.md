# BCIPL Full E2E Browser Test — Chrome + Excel Comparison

**Purpose:** Paste this entire prompt into a fresh Claude Code session. It will run a complete end-to-end test of the CMA Automation System through the real browser UI (Playwright + Chrome), then compare the generated CMA Excel against the ground truth file cell-by-cell.

**What this tests:** The entire user journey — create client, upload 3 financial documents, extract data, verify extraction, create CMA report, let classification run, review/approve items, generate Excel, download it, and compare every INPUT SHEET cell against the CA-prepared ground truth.

---

## CONSTRAINTS — READ THESE FIRST

1. **NEVER** create unbounded loops. Max 20 polls for any wait. Max 100 total API calls. Max 3 retries per failed action.
2. **NEVER** modify any source code. This is a READ-ONLY test. You are testing the app as-is.
3. Take a screenshot after EVERY major step. Save all screenshots to `DOCS/test-results/bcipl/run-YYYY-MM-DD/`.
4. If something fails, screenshot it, log the error, and continue to the next step if possible. Do NOT retry endlessly.
5. Total test budget: maximum 30 minutes wall-clock time. If you exceed this, stop and report what you have.
6. Use Playwright MCP tools (browser_navigate, browser_click, browser_fill_form, browser_snapshot, browser_take_screenshot, browser_file_upload, browser_wait_for). If Playwright MCP is not available, fall back to a Python Playwright script.

---

## COMPANY DETAILS

| Field | Value |
|-------|-------|
| Company Name | BCIPL |
| Industry | Manufacturing |
| Source Files | 3 × `.xls` in `FInancials main/BCIPL/` |
| Ground Truth CMA | `FInancials main/BCIPL/CMA BCIPL 12012024.xls` |
| Source Unit | `rupees` (all 3 documents) |
| CMA Output Unit | `crores` |
| Financial Years | FY2021, FY2022, FY2023 |
| Nature | All Audited |

### Source Files (exact paths from project root)

```
FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls   → FY2021, rupees
FInancials main/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls   → FY2022, rupees
FInancials main/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls  → FY2023, rupees
```

### Ground Truth File

```
FInancials main/BCIPL/CMA BCIPL 12012024.xls
```

This is the CMA prepared manually by the CA firm. You will read its `INPUT SHEET` and compare against the generated Excel's `INPUT SHEET`.

---

## STEP 0: PRE-FLIGHT CHECKS

Before touching the browser, verify the infrastructure is running.

### 0a. Check Docker Services

```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
docker compose ps
```

All 4 services must be running: `backend`, `frontend`, `worker`, `redis`.

If services are down:
```bash
docker compose up -d
```

Wait 15 seconds, then re-check.

### 0b. Health Check

```bash
curl http://localhost:8000/health
```

Must return `{"status": "ok", ...}`. If it returns an error, check `docker compose logs --tail=20 backend`.

### 0c. Frontend Check

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3002
```

Must return `200`. If not, check `docker compose logs --tail=20 frontend`.

### 0d. Create Output Directory

```bash
mkdir -p "DOCS/test-results/bcipl/run-$(date +%Y-%m-%d)"
```

This is where all screenshots and results will be saved.

### 0e. Record Pre-flight Results

Save a `preflight.json` to the output directory:
```json
{
  "timestamp": "ISO-8601",
  "docker_services": "all_up | partial | down",
  "backend_health": "ok | error",
  "frontend_status": 200,
  "output_dir": "DOCS/test-results/bcipl/run-YYYY-MM-DD"
}
```

**STOP if any pre-flight check fails. Do not proceed to browser testing with broken infrastructure.**

---

## STEP 1: OPEN THE APP

1. Launch browser and navigate to `http://localhost:3002`
2. The app uses `DISABLE_AUTH=true` in dev mode, so no login is needed. You should land on the dashboard or clients page.
3. **Screenshot:** `step-01-app-loaded.png`

**What to verify:**
- Page loads without errors
- Sidebar navigation is visible
- No blank white screen or error boundary

---

## STEP 2: CREATE A NEW CLIENT

1. Navigate to `/clients` (click "Clients" in sidebar or go directly)
2. **Screenshot:** `step-02-clients-page.png`
3. Click the "New Client" button (look for a button with "New Client" or a "+" icon linking to `/clients/new`)
4. Fill the form:
   - **Client Name:** `BCIPL`
   - **Industry Type:** Select `Manufacturing` from the dropdown
   - Leave other fields as defaults (FY ending: 31st March, Currency: INR)
5. Click "Create Client" or the submit button
6. You should be redirected to `/clients/{client_id}` — the client detail page
7. **Screenshot:** `step-03-client-created.png`

**What to verify:**
- Client name "BCIPL" appears on the page
- Industry badge shows "Manufacturing"
- Documents section is empty
- A "Upload" button is visible

**Save the client_id from the URL** (e.g., `/clients/abc-123-def` → client_id is `abc-123-def`).

---

## STEP 3: UPLOAD 3 DOCUMENTS

Navigate to the upload page: click the "Upload" button on the client detail page (links to `/clients/{client_id}/upload`).

**Screenshot:** `step-04-upload-page.png`

### Upload Document 1: FY2021

1. The upload form has a file dropzone (react-dropzone) and metadata fields
2. Upload the file: `FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls`
   - Use Playwright's `browser_file_upload` to set the file on the hidden `<input type="file">` inside the dropzone
   - The dropzone `<input>` accepts `.pdf, .xlsx, .xls` files
3. Set metadata fields:
   - **Document Type:** `Combined Financial Statement` (value: `combined_financial_statement`)
   - **Financial Year:** `2021`
   - **Nature:** `Audited` (value: `audited`)
   - **Source Unit:** `Rupees` (value: `rupees`)
4. Click the "Upload" button
5. Wait for success toast or upload completion
6. **Screenshot:** `step-05-upload-doc1.png`

### Upload Document 2: FY2022

Repeat the same process:
- File: `FInancials main/BCIPL/6. BCIPL_ Final Accounts_2021-22.xls`
- Financial Year: `2022`
- All other fields same as Doc 1

**Screenshot:** `step-06-upload-doc2.png`

### Upload Document 3: FY2023

Repeat:
- File: `FInancials main/BCIPL/BCIPL_ FY 2023 Final Accounts_25092023.xls`
- Financial Year: `2023`
- All other fields same as Doc 1

**Screenshot:** `step-07-upload-doc3.png`

**What to verify after all 3 uploads:**
- All 3 documents appear in the document list on the upload page
- Each shows the correct filename and FY
- No error toasts

**Screenshot:** `step-08-all-docs-uploaded.png`

---

## STEP 4: EXTRACT DATA FROM EACH DOCUMENT

For each of the 3 documents, you need to trigger extraction and verify it.

The extraction flow works per-document through the verify page at `/cma/{document_id}/verify`.

### For each document (repeat 3 times):

1. From the client detail page (`/clients/{client_id}`), find the document in the list
2. Click on the document (or its "Verify" / "Extract" action) — this navigates to `/cma/{document_id}/verify`
3. The verify page will show one of these states:
   - **Sheet selection:** For Excel files, it shows available sheets with checkboxes. The app pre-selects recommended sheets (BS, P&L, Notes, etc.) and excludes noise sheets (Trial Balance, Pivot, Memo, etc.). Accept the defaults and click "Extract" or "Start Extraction".
   - **Extraction in progress:** Shows a progress bar or spinner. Wait for it to complete (poll up to 20 times, ~5 seconds each = max 100 seconds per doc).
   - **Verification screen:** Shows extracted line items in a table. Review the items.

4. Once extraction is complete, the page shows the extracted items (ExtractionVerifier component):
   - It displays a table of line items with description, amount, section
   - There's a "Verify" or "Confirm" button to approve the extraction
   - Click it to mark this document as verified

5. **Screenshot after each document extraction + verification:**
   - `step-09-doc1-extracted.png`
   - `step-10-doc2-extracted.png`
   - `step-11-doc3-extracted.png`

**What to verify per document:**
- Extraction completes (status changes to "extracted")
- Item count is between 30 and 300 (if >300, sheet filtering may have failed)
- Key items visible: look for Revenue, Raw Materials, Wages, Share Capital, Trade Payables, etc.
- After clicking Verify, status changes to "verified"

**IMPORTANT:** Record the item count for each document:
```
doc1 (FY2021): XX items
doc2 (FY2022): XX items
doc3 (FY2023): XX items
```

If any document shows >300 items, that's a bug (Trial Balance not filtered). Note it but continue.

---

## STEP 5: CREATE A CMA REPORT

1. Navigate back to the client detail page: `/clients/{client_id}`
2. All 3 documents should now show "Verified" status
3. In the "CMA Reports" section, click "New Report" (links to `/clients/{client_id}/cma/new`)
4. **Screenshot:** `step-12-new-report-page.png`
5. Fill the form:
   - **Report Title:** `BCIPL CMA FY2021-FY2023`
   - **CMA Output Unit:** Select `Crores` from the dropdown (value: `crores`)
   - **Select Documents:** Click all 3 documents to select them (they appear as clickable cards — click each one so it shows "Selected" badge)
6. Click "Create Report"
7. You should be redirected to the CMA overview page: `/cma/{report_id}`
8. **Screenshot:** `step-13-report-created.png`

**Save the report_id from the URL.**

**What to verify:**
- Report title shows "BCIPL CMA FY2021-FY2023"
- Status shows "classifying" or "in_progress" or similar
- Classification summary shows total items
- 3 documents are linked

---

## STEP 6: WAIT FOR CLASSIFICATION TO COMPLETE

Classification runs automatically after report creation. The CMA overview page (`/cma/{report_id}`) shows a confidence dashboard that updates as items are classified.

1. The classification is handled by the ARQ worker — it processes items through the 3-tier pipeline (fuzzy → AI Haiku → doubt)
2. This can take 2-5 minutes depending on the number of items and AI response times
3. Poll the page: refresh every 15-20 seconds (navigate to `/cma/{report_id}` again) and check:
   - The confidence numbers are increasing
   - The status changes from "classifying" to "classified" or "review_pending"
4. **Max 20 refreshes** (= ~5-7 minutes). If classification hasn't completed after 20 refreshes, check worker logs:
   ```bash
   docker compose logs --tail=50 worker
   ```
   Screenshot the logs and note the issue, then continue.

5. **Screenshot:** `step-14-classification-done.png`

**What to verify:**
- Classification summary shows numbers (total, high confidence, needs review, doubts)
- The "Review" button is clickable
- Note the confidence breakdown:
  ```
  Total: XX
  Auto-approved (≥0.85): XX
  Needs review: XX
  Doubts: XX
  ```

---

## STEP 7: REVIEW AND APPROVE CLASSIFICATIONS

1. Click "Review" button on the CMA overview page → navigates to `/cma/{report_id}/review`
2. **Screenshot:** `step-15-review-page.png`
3. The review page shows classifications with a filter toggle:
   - Default view: "Needs Review Only" — shows items needing attention
   - Toggle to "Show All" to see everything
4. Screenshot both views:
   - `step-16-review-needs-review.png` (filtered view)
   - `step-17-review-all.png` (all items view — toggle the filter button)

### Bulk Approve

5. Look for a "Bulk Approve" or "Approve All" button — it approves all high-confidence items that aren't doubts
6. Click it
7. **Screenshot:** `step-18-after-bulk-approve.png`

### Handle Remaining Items

8. After bulk approve, some items may still need review (doubts, low confidence)
9. For remaining items: if there's a way to approve them individually or in bulk, do so
   - If the UI has individual "Approve" buttons per item, click approve on each remaining item
   - If there are too many (>50), note the count and proceed — the app may allow generating with some unreviewed items
10. **Screenshot:** `step-19-review-complete.png`

**What to verify:**
- After bulk approve, the count of "needs review" items decreases significantly
- Note how many items remain unresolved

**IMPORTANT:** The Generate Excel button on the CMA overview page requires ALL items to be reviewed (no `needs_review` items remaining). If items remain, you need to approve them individually or the generation will be blocked.

If the UI provides a way to force-approve all remaining items, use it. If not, you will need to use the API directly:

```bash
# Only use this fallback if the UI doesn't allow approving all items
# Get all classifications for the report
curl http://localhost:8000/api/cma-reports/{REPORT_ID}/classifications > /tmp/classifications.json

# For each item with status != "approved", approve it via API
# PATCH http://localhost:8000/api/classifications/{classification_id}
# Body: { "status": "approved" }
```

Document whether you used the UI or API fallback.

---

## STEP 8: GENERATE THE CMA EXCEL

1. Navigate back to CMA overview: `/cma/{report_id}`
2. The "Generate Excel" button should now be enabled (all items reviewed)
3. Click "Generate Excel" — this navigates to `/cma/{report_id}/generate`
4. The generate page automatically triggers generation and shows progress:
   - "Starting..." → "Generating..." → "Complete" or "Failed"
5. Wait for completion (the page polls automatically every 2 seconds)
6. **Screenshot:** `step-20-generation-progress.png`
7. Once complete, a "Download" button appears
8. **Screenshot:** `step-21-generation-complete.png`

**What to verify:**
- Generation completes without error
- Download button is visible
- Status shows "Complete"

---

## STEP 9: DOWNLOAD THE GENERATED EXCEL

1. Click the "Download" button on the generate page
2. The browser will download the `.xlsm` file
3. Alternatively, use the API to get the download URL:
   ```bash
   curl http://localhost:8000/api/cma-reports/{REPORT_ID}/download
   ```
   This returns `{ "signed_url": "https://..." }`. Download the file:
   ```bash
   curl -L "{SIGNED_URL}" -o "DOCS/test-results/bcipl/run-YYYY-MM-DD/BCIPL_generated_CMA.xlsm"
   ```

4. **Verify the downloaded file exists and is >50KB** (a valid .xlsm file should be ~100-170KB)

**Screenshot:** `step-22-file-downloaded.png`

---

## STEP 10: COMPARE GENERATED EXCEL VS GROUND TRUTH

This is the most important step. Write and run a Python script that compares the two Excel files.

### Create the comparison script

Save this script to `DOCS/test-results/bcipl/run-YYYY-MM-DD/compare_cma.py` and run it.

**The script must:**

1. **Read the ground truth file** using `xlrd` (because it's `.xls` format):
   - File: `FInancials main/BCIPL/CMA BCIPL 12012024.xls`
   - Sheet: `INPUT SHEET` — find this sheet by name (exact match, case-insensitive if needed)
   - Read ALL numeric cells in **rows 17 to 262** (P&L rows 17-109, BS rows 111-262), **columns B, C, D** (indices 1, 2, 3 in xlrd)
   - Skip any cell that is empty, None, blank string, or contains text (non-numeric)

2. **Read the generated file** using `openpyxl` (because it's `.xlsm` format):
   - File: `DOCS/test-results/bcipl/run-YYYY-MM-DD/BCIPL_generated_CMA.xlsm`
   - Sheet: `INPUT SHEET`
   - Read the same rows (17-262) and columns (B, C, D)
   - Skip empty/None cells

3. **Sanity check — print first 10 ground truth values:**
   Before comparing, print the first 10 non-empty cells from the ground truth file so the user can eyeball-verify it's reading the right data:
   ```
   GROUND TRUTH SANITY CHECK (first 10 values):
   Row 22, Col B: 96.58
   Row 22, Col C: 234.64
   ...
   ```

4. **Compare each cell where the ground truth has a value:**
   - **MATCH:** Generated value is within 2% of ground truth value, OR both values are 0 (or both < 0.01 in absolute terms)
   - **MISMATCH:** Generated value exists but differs by more than 2%
   - **MISSING:** Ground truth has a value but generated cell is empty/0/None
   - **EXTRA:** Generated has a value but ground truth is empty (log these separately, don't count as errors)

   **2% tolerance formula:**
   ```python
   def is_match(expected, actual, tolerance=0.02):
       if abs(expected) < 0.01 and abs(actual) < 0.01:
           return True  # both effectively zero
       if expected == 0:
           return abs(actual) < 0.01
       return abs(actual - expected) / abs(expected) <= tolerance
   ```

5. **Output a detailed comparison table** saved to `comparison_results.md`:

   ```markdown
   # BCIPL CMA Comparison Results
   **Date:** YYYY-MM-DD
   **Ground Truth:** FInancials main/BCIPL/CMA BCIPL 12012024.xls
   **Generated:** DOCS/test-results/bcipl/run-YYYY-MM-DD/BCIPL_generated_CMA.xlsm

   ## Summary
   | Metric | Count |
   |--------|-------|
   | Ground truth cells | XX |
   | Matching | XX |
   | Mismatched | XX |
   | Missing | XX |
   | Extra (generated only) | XX |
   | **Accuracy** | **XX.X%** |

   ## Mismatched Cells (most important)
   | Row | Col | Label | Expected | Got | Diff% |
   |-----|-----|-------|----------|-----|-------|
   | ... | ... | ...   | ...      | ... | ...   |

   ## Missing Cells (ground truth has value, generated is empty)
   | Row | Col | Label | Expected |
   |-----|-----|-------|----------|
   | ... | ... | ...   | ...      |

   ## All Matching Cells
   | Row | Col | Expected | Got |
   |-----|-----|----------|-----|
   | ... | ... | ...      | ... |
   ```

6. **For the "Label" column** in the tables above: Read the label from column A of the ground truth file for that row. This makes the results human-readable.

7. **Print a final verdict:**
   ```
   ═══════════════════════════════════════
   VERDICT: XX/YY cells correct (ZZ.Z%)
   Mismatches: NN
   Missing: MM
   ═══════════════════════════════════════
   ```

### Run the script

```bash
cd "C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2"
pip install xlrd openpyxl  # if not already installed
python "DOCS/test-results/bcipl/run-YYYY-MM-DD/compare_cma.py"
```

If `xlrd` or `openpyxl` are not available in the host, run inside Docker:
```bash
docker compose exec backend pip install xlrd
docker compose exec backend python /app/path/to/compare_cma.py
```

---

## STEP 11: COMPILE FINAL TEST REPORT

Create `DOCS/test-results/bcipl/run-YYYY-MM-DD/TEST_REPORT.md` with:

```markdown
# BCIPL E2E Browser Test Report
**Date:** YYYY-MM-DD
**Tester:** Claude Code automated harness

## 1. Pre-flight
- Docker services: ✅/❌
- Backend health: ✅/❌
- Frontend accessible: ✅/❌

## 2. Client Creation
- Client created: ✅/❌
- Client ID: `{client_id}`

## 3. Document Upload
| Document | FY | Upload Status |
|----------|----|---------------|
| BCIPL Final Accounts 2020-21 | 2021 | ✅/❌ |
| BCIPL Final Accounts 2021-22 | 2022 | ✅/❌ |
| BCIPL FY 2023 Final Accounts | 2023 | ✅/❌ |

## 4. Extraction
| Document | FY | Items Extracted | Status |
|----------|----|----------------|--------|
| Doc 1 | 2021 | XX | verified ✅/❌ |
| Doc 2 | 2022 | XX | verified ✅/❌ |
| Doc 3 | 2023 | XX | verified ✅/❌ |

**Item count check:** All docs between 30-300 items? ✅/❌
**If >300:** Trial Balance filtering bug likely present

## 5. Classification
| Metric | Value |
|--------|-------|
| Total items | XX |
| Auto-approved (≥0.85 confidence) | XX |
| Needs review | XX |
| Doubts | XX |
| Fuzzy matches | XX |
| AI matches | XX |
| AI failures | XX |

## 6. Review & Approval
- Bulk approve used: ✅/❌
- Items remaining after bulk approve: XX
- Method to clear remaining: UI / API fallback
- All items approved: ✅/❌

## 7. Excel Generation
- Generation triggered: ✅/❌
- Generation completed: ✅/❌
- File downloaded: ✅/❌
- File size: XX KB

## 8. Excel Comparison (INPUT SHEET only)
| Metric | Count |
|--------|-------|
| Ground truth cells | XX |
| Matching (within 2%) | XX |
| Mismatched | XX |
| Missing | XX |
| **Accuracy** | **XX.X%** |

### Top Mismatches
| Row | Label | Expected | Got | Diff% |
|-----|-------|----------|-----|-------|
| ... | ...   | ...      | ... | ...   |

### Missing Values
| Row | Label | Expected |
|-----|-------|----------|
| ... | ...   | ...      |

## 9. Bugs Found
1. [Bug description]
2. [Bug description]

## 10. Screenshots
- step-01-app-loaded.png
- step-02-clients-page.png
- ... (list all screenshots taken)

## 11. Overall Verdict
**PASS / PARTIAL PASS / FAIL**
[1-2 sentence summary of the result]
```

---

## STEP 12: SAVE ALL ARTIFACTS

Ensure all files are saved in the output directory `DOCS/test-results/bcipl/run-YYYY-MM-DD/`:

```
DOCS/test-results/bcipl/run-YYYY-MM-DD/
├── preflight.json
├── step-01-app-loaded.png
├── step-02-clients-page.png
├── step-03-client-created.png
├── step-04-upload-page.png
├── step-05-upload-doc1.png
├── step-06-upload-doc2.png
├── step-07-upload-doc3.png
├── step-08-all-docs-uploaded.png
├── step-09-doc1-extracted.png
├── step-10-doc2-extracted.png
├── step-11-doc3-extracted.png
├── step-12-new-report-page.png
├── step-13-report-created.png
├── step-14-classification-done.png
├── step-15-review-page.png
├── step-16-review-needs-review.png
├── step-17-review-all.png
├── step-18-after-bulk-approve.png
├── step-19-review-complete.png
├── step-20-generation-progress.png
├── step-21-generation-complete.png
├── step-22-file-downloaded.png
├── BCIPL_generated_CMA.xlsm
├── compare_cma.py
├── comparison_results.md
└── TEST_REPORT.md
```

---

## QUICK REFERENCE — KEY URLS

| Page | URL |
|------|-----|
| App root | `http://localhost:3002` |
| Clients list | `http://localhost:3002/clients` |
| New client | `http://localhost:3002/clients/new` |
| Client detail | `http://localhost:3002/clients/{client_id}` |
| Upload docs | `http://localhost:3002/clients/{client_id}/upload` |
| Verify/Extract doc | `http://localhost:3002/cma/{document_id}/verify` |
| New CMA report | `http://localhost:3002/clients/{client_id}/cma/new` |
| CMA overview | `http://localhost:3002/cma/{report_id}` |
| Classification review | `http://localhost:3002/cma/{report_id}/review` |
| Generate Excel | `http://localhost:3002/cma/{report_id}/generate` |
| API health | `http://localhost:8000/health` |

## QUICK REFERENCE — API FALLBACKS

Only use these if the browser UI doesn't work for a specific step:

```bash
# Create client
curl -X POST http://localhost:8000/api/clients/ \
  -H "Content-Type: application/json" \
  -d '{"name":"BCIPL","industry_type":"manufacturing"}'

# Upload document
curl -X POST http://localhost:8000/api/documents/ \
  -F "client_id={CLIENT_ID}" \
  -F "document_type=combined_financial_statement" \
  -F "financial_year=2021" \
  -F "nature=audited" \
  -F "source_unit=rupees" \
  -F "file=@FInancials main/BCIPL/6. BCIPL_ Final Accounts_2020-21.xls"

# Trigger extraction
curl -X POST http://localhost:8000/api/extraction/{DOC_ID}/extract

# Check extraction status
curl http://localhost:8000/api/documents/?client_id={CLIENT_ID}

# Verify document
curl -X POST http://localhost:8000/api/extraction/{DOC_ID}/verify

# Trigger classification
curl -X POST http://localhost:8000/api/extraction/{DOC_ID}/classify

# Create CMA report
curl -X POST http://localhost:8000/api/clients/{CLIENT_ID}/cma-reports \
  -H "Content-Type: application/json" \
  -d '{"title":"BCIPL CMA FY2021-FY2023","document_ids":["{DOC1}","{DOC2}","{DOC3}"],"cma_output_unit":"crores"}'

# Bulk approve all classifications
curl http://localhost:8000/api/cma-reports/{REPORT_ID}/classifications | \
  python3 -c "import json,sys; items=json.load(sys.stdin); [print(i['id']) for i in items if i.get('status')!='approved']"
# Then PATCH each one

# Generate Excel
curl -X POST http://localhost:8000/api/cma-reports/{REPORT_ID}/generate

# Download Excel
curl http://localhost:8000/api/cma-reports/{REPORT_ID}/download
# Returns { "signed_url": "..." }

# Worker logs (if anything is slow/stuck)
docker compose logs --tail=50 worker
```

---

## FAILURE MODES — WHAT TO DO

| Problem | Action |
|---------|--------|
| Docker service not running | `docker compose up -d`, wait 15s, retry once |
| Frontend blank/error | Screenshot, check `docker compose logs frontend`, note in report |
| File upload fails in browser | Try API fallback curl command |
| Extraction stuck >2 min | Check `docker compose logs worker`, screenshot, note, continue |
| >300 items extracted | Note as Trial Balance bug, continue |
| Classification stuck >5 min | Check worker logs, screenshot, note, continue |
| Bulk approve button not visible | Approve items individually, or use API fallback |
| Generate button disabled | Check if items still need review, resolve them first |
| Generation fails | Check worker logs, note error, try API fallback |
| Download returns error | Try API download endpoint directly |
| Ground truth file can't be read | Try both xlrd and openpyxl, check sheet names |
| Python deps missing | `pip install xlrd openpyxl` or run inside Docker container |

---

**END OF TEST PROMPT — Paste everything above into a fresh Claude Code session to run the test.**

---
---

# LESSONS LEARNED — Read Before Running ANY E2E Test

These lessons come from real test failures. Violating any of these will produce invalid results.

## Lesson 1: ALWAYS use a fresh client — NEVER reuse pre-classified data

**What happened:** BCIPL test on 2026-03-23 took 60+ minutes to classify 691 items. The tester pivoted to an existing pre-classified client from a previous session. That old client had FY2022 uploaded with `source_unit=lakhs` instead of `rupees`. Result: column C values were 100,000x wrong, accuracy dropped from 98.2% to 3.3%.

**Rule:** NEVER pivot to an existing client if classification is slow. Either:
- Wait for classification to finish (budget 60-90 min for 3 docs)
- Stop the test and report "classification timeout" — a partial result is better than a wrong result
- If you must reuse a client, verify EVERY document's `source_unit` matches what the test expects

## Lesson 2: Confirm ground truth units BEFORE comparing

**What happened:** The comparison script read ground truth values but nobody confirmed whether the file was in lakhs or crores. The generated Excel used crores, the ground truth was in crores, but intermediate values were in wrong units due to metadata bugs. This made it impossible to distinguish "real mismatch" from "unit confusion."

**Rule:** Before comparing, read cell **B13** from the ground truth file's INPUT SHEET — it always contains the unit (e.g., `'In crs'`, `'In Lakhs'`). Then:
1. Read B13 — this is the ground truth unit
2. Confirm the CMA output unit used during report creation matches B13
3. If they don't match, the comparison is invalid — stop and fix
4. Print first 10 ground truth values as a sanity check

## Lesson 3: Exclude formula/subtotal rows from comparison

**What happened:** The comparison checked 738 cells (rows 17-262). The ground truth had hardcoded values in subtotal rows (R24, R26, R52, R57, R61, R80, etc.) that our template computes via Excel macros. These showed as "MISSING" — 150 cells that were false negatives.

**Rule:** The comparison script should identify which rows are subtotals/formulas in the CMA template. Two approaches:
- **Option A (recommended):** Only compare rows where the Excel generator actually writes data — skip formula rows
- **Option B:** Flag formula rows separately in the report: "X subtotal rows excluded from accuracy calculation"

The rows the generator writes to are defined in `backend/app/mappings/cma_field_rows.py`. Any row NOT in that file is a formula/subtotal row and should be excluded from the comparison.

## Lesson 4: source_unit must be set correctly per document

**What happened:** FY2022 Excel for BCIPL had values in lakhs (not rupees). The test prompt said "all rupees" but the actual file content was in lakhs. When uploaded as rupees, the conversion ÷10,000,000 made values too small. When uploaded as lakhs (correctly for that file), conversion works with ÷100 for crores output.

**Rule:** Before writing the test prompt for a company:
1. Open each source document and check what unit the numbers are in
2. Look for headers like "Rs. in Lakhs", "Amount in '000s", or raw rupee values (7+ digits)
3. Set `source_unit` per document — they can differ across financial years
4. Document the unit in the test prompt per file, not as a blanket "all rupees"

## Lesson 5: Classification takes 20-30 minutes per document

**What happened:** The 30-minute wall-clock budget was insufficient. Classification alone took 60+ minutes for 3 documents (21.5 + 14 + 23 min).

**Rule:** Budget at least 90 minutes total wall-clock for a 3-document E2E test:
- Upload + extraction: ~5 min
- Classification: ~60 min (20 min per doc, sequential due to max_jobs=1)
- Review + generation: ~10 min
- Comparison: ~5 min
- Buffer: ~10 min

If classification is slow, check `docker compose logs --tail=50 worker` for rate limit errors. Do NOT skip or shortcut classification — wait for it.

## Lesson 6: GET /api/documents/{id} returns 405

**What happened:** The verify page (`/cma/{document_id}/verify`) calls `GET /api/documents/{id}` which returns 405 Method Not Allowed. The browser verify flow breaks for ALL documents.

**Workaround:** Use API fallback — trigger extraction via `POST /api/extraction/{DOC_ID}/extract`, then verify via `POST /api/extraction/{DOC_ID}/verify`. This bug needs to be fixed in `backend/app/routers/documents.py`.

## Lesson 7: Navigate to /clients, not /

**What happened:** `http://localhost:3002/` redirects to `/login` even with `DISABLE_AUTH=true`.

**Workaround:** Always navigate directly to `http://localhost:3002/clients` to start the test.

## Lesson 8: The accuracy number depends on WHAT you compare

| Comparison scope | March 22 result | March 23 result | Why different |
|-----------------|-----------------|-----------------|---------------|
| ~170 data-entry cells only | 98.2% (170/173) | Not measured | Excludes formula rows |
| 333 non-blank cells (rows 17-262) | Not measured | 3.3% (11/333) | Includes subtotals + unit bug |

**Rule:** Always report TWO accuracy numbers:
1. **Data-entry accuracy:** Only cells the Excel generator writes (from `cma_field_rows.py`)
2. **Full sheet accuracy:** All non-blank cells in rows 17-262 (includes formula rows)

The first number measures classification + Excel generation quality. The second measures whether the full CMA matches the CA's work (requires macros to run).
