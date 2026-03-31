# CMA Test Harness — BCIPL End-to-End Test

> PASTE THIS INTO A NEW CLAUDE CODE WINDOW.
> READ THIS ENTIRE PROMPT BEFORE DOING ANYTHING.
> Execute exactly what is described here, in exact order.
> COST GUARD: The classifier uses Anthropic Haiku (~$0.80/M input tokens). Classification will make ~100-200 API calls automatically via the backend worker — this is expected and costs ~$0.10-0.30 total. No cost guard needed for this test.

---

## System State

```
Backend:      http://localhost:8000
Frontend:     http://localhost:3002
Redis:        localhost:6379
Auth bypass:  DISABLE_AUTH=true
Project root: C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2
```

Headers for ALL API calls:
```
X-User-Id: 00000000-0000-0000-0000-000000000001
X-User-Role: admin
```

## Context

- Client: **BCIPL** (manufacturing company)
- Client ID: `19cf7c12-2f2a-4c98-b2b3-7011a999a310`
- 3 documents already uploaded and reset to `pending` status
- All stale data has been purged — clean slate
- Classifier: **Claude Haiku** via OpenRouter (`tool_choice` forced to `classify_line_item`)
- Extractor: Fixed Excel extractor with auto sheet filtering + subnotes exclusion + column scanning A-F
- Unit conversion: **per-document** (each doc has its own source_unit → output divisor)
- Excel generator: Uses `cma_row` directly from classifications (not ALL_FIELD_TO_ROW lookup)
- API endpoints: All classification endpoints join `extracted_line_items` for description+amount

## Documents (already in DB — DO NOT re-upload)

| Doc ID | File Name | FY | Type | Source Unit | Expected Divisor (output=lakhs) |
|--------|-----------|-----|------|-------------|------|
| `51ac85c0-a142-44ef-9522-ff45bbb904b5` | 6. BCIPL_ Final Accounts_2020-21.xls | 2021 | xls | rupees | ÷100,000 |
| `4657c66b-f74e-4d0c-bab7-951789abff87` | 6. BCIPL_ Final Accounts_2021-22.xls | 2022 | xls | **lakhs** | ÷1 (no conversion) |
| `194534d5-fffe-4029-8c2f-738b06772b4c` | BCIPL_ FY 2023 Final Accounts_25092023.xls | 2023 | xls | rupees | ÷100,000 |

### CRITICAL: Mixed Unit Warning
FY2022 is in Lakhs (`[in 100,000]` header), FY2021 and FY2023 are in full Rupees.
The generator now does **per-document** unit conversion, so FY2022 values pass through unchanged
while FY2021/FY2023 values are divided by 100,000.

---

## PHASE 0: Reset BCIPL Data (Clean Slate)

Before running the test, purge all stale data from previous test runs.

### Step 0a: Purge old data via Supabase SQL

Run these SQL statements in order via the Supabase MCP `execute_sql` tool:

```sql
-- 1. Delete classifications for BCIPL documents
DELETE FROM classifications
WHERE line_item_id IN (
  SELECT id FROM extracted_line_items
  WHERE document_id IN (
    '51ac85c0-a142-44ef-9522-ff45bbb904b5',
    '4657c66b-f74e-4d0c-bab7-951789abff87',
    '194534d5-fffe-4029-8c2f-738b06772b4c'
  )
);

-- 2. Delete extracted line items
DELETE FROM extracted_line_items
WHERE document_id IN (
  '51ac85c0-a142-44ef-9522-ff45bbb904b5',
  '4657c66b-f74e-4d0c-bab7-951789abff87',
  '194534d5-fffe-4029-8c2f-738b06772b4c'
);

-- 3. Delete CMA reports for this client
DELETE FROM cma_report_history
WHERE cma_report_id IN (
  SELECT id FROM cma_reports WHERE client_id = '19cf7c12-2f2a-4c98-b2b3-7011a999a310'
);
DELETE FROM cma_reports
WHERE client_id = '19cf7c12-2f2a-4c98-b2b3-7011a999a310';

-- 4. Reset documents to pending
UPDATE documents
SET extraction_status = 'pending', verification_status = 'pending'
WHERE id IN (
  '51ac85c0-a142-44ef-9522-ff45bbb904b5',
  '4657c66b-f74e-4d0c-bab7-951789abff87',
  '194534d5-fffe-4029-8c2f-738b06772b4c'
);

-- 5. Verify FY2022 source_unit is 'lakhs' (not 'rupees')
UPDATE documents SET source_unit = 'lakhs'
WHERE id = '4657c66b-f74e-4d0c-bab7-951789abff87';
```

### Step 0b: Verify clean state
```sql
SELECT id, file_name, extraction_status, verification_status, source_unit
FROM documents
WHERE id IN (
  '51ac85c0-a142-44ef-9522-ff45bbb904b5',
  '4657c66b-f74e-4d0c-bab7-951789abff87',
  '194534d5-fffe-4029-8c2f-738b06772b4c'
);
```

All 3 should show `extraction_status = 'pending'`, `verification_status = 'pending'`.
FY2022 doc should show `source_unit = 'lakhs'`.

---

## PHASE 1: Extraction (3 documents)

For EACH document, in order (FY2021 → FY2022 → FY2023):

### Step 1a: Preview sheets
```
GET /api/documents/{doc_id}/sheets
```
- Log all sheet names and which are `auto_included: true`
- Verify financial sheets (BS, P&L, Notes, Trial Balance, etc.) are included
- Verify noise sheets (Memo, Def Tax, Capital WIP, EMI, Pivot, Ratios) are excluded
- Save the full sheet list for each document in the report

### Step 1b: Trigger extraction (use auto-detected sheets)
```
POST /api/documents/{doc_id}/extract
Content-Type: application/json

{}
```

### Step 1c: Poll for completion
```
GET /api/documents/{doc_id}
```
Poll every 10 seconds. **MAX 30 polls** (5 minutes). Stop if `extraction_status` is `extracted` or `failed`.

### Step 1d: Fetch and validate items
```
GET /api/documents/{doc_id}/items
```

Log per document:
- Total item count
- First 10 items (description + amount + section)
- Sections found with counts
- Any suspicious amounts: < 100 or > 100,000,000 for rupees docs; > 1,000,000 for lakhs doc (FY2022)

### Extraction Gates

| Document | Min Items | Max Items | Notes |
|----------|-----------|-----------|-------|
| FY2021 | 30 | 200 | Rupees. BS + P&L + Notes |
| FY2022 | 30 | 200 | **Lakhs**. Amounts typically 100–50,000 range |
| FY2023 | 30 | 200 | Rupees. Same structure |

**HARD GATE**: ANY document with 0 items or > 300 items → STOP.
**SOFT GATE**: Total across 3 docs < 100 → flag warning, continue.

### Step 1e: Verify each document
```
POST /api/documents/{doc_id}/verify
```
Do this for ALL 3 documents after extraction succeeds.

---

## PHASE 2: Classification

### Step 2a: Create CMA Report
```
POST /api/cma-reports/
Content-Type: application/json

{
  "title": "BCIPL CMA Test - 2026-03-22",
  "document_ids": [
    "51ac85c0-a142-44ef-9522-ff45bbb904b5",
    "4657c66b-f74e-4d0c-bab7-951789abff87",
    "194534d5-fffe-4029-8c2f-738b06772b4c"
  ],
  "cma_output_unit": "lakhs"
}
```
Save the returned `report_id`.

### Step 2b: Trigger classification
```
POST /api/cma-reports/{report_id}/classify
```

### Step 2c: Poll for classification completion
```
GET /api/cma-reports/{report_id}/confidence
```
Poll every 15 seconds. **MAX 40 polls** (10 minutes).
Classification is done when `total == (high_confidence + medium_confidence + needs_review + approved + corrected)`.

### Step 2d: Fetch all classifications
```
GET /api/cma-reports/{report_id}/classifications
```

Log:
- Total classifications count
- `is_doubt: true` count
- `cma_field_name: null` count (should be 0 for non-doubt items)
- `line_item_description: null` count (**MUST be 0** — tests the join fix)
- Doubt reasons containing "unavailable" (**MUST be 0** — tests Claude Haiku works)
- 10 highest-confidence matches (description → cma_field_name, confidence, reasoning)
- 10 doubt items (description → doubt_reason)
- Classification method breakdown (fuzzy_match vs ai_haiku counts)

### Classification Gates

| Metric | Target | Gate |
|--------|--------|------|
| Total classified | = total extracted items | HARD |
| AI failures ("unavailable" in doubt_reason) | 0 | HARD — Claude Haiku API issue |
| `line_item_description` is null | 0 | HARD — join fix broken |
| Doubt rate | < 40% | SOFT |
| High confidence (>= 0.8) | > 50% | SOFT |

**CRITICAL STOP**: If > 5 classifications have `doubt_reason` containing "unavailable", STOP immediately — the Anthropic API integration is broken.

---

## PHASE 3: Generate CMA Excel (THE MAIN TEST)

### Step 3a: Check for unresolved doubts
```
GET /api/cma-reports/{report_id}/confidence
```
Log the `needs_review` count. If `needs_review > 0`, the generate endpoint will BLOCK.

### Step 3b: Force-approve doubts for testing (if needed)
If doubts exist, approve them all so we can test Excel generation:
```sql
-- Run this via Supabase SQL editor or direct SQL
UPDATE classifications
SET is_doubt = false, status = 'approved'
WHERE line_item_id IN (
  SELECT eli.id FROM extracted_line_items eli
  WHERE eli.document_id IN (
    '51ac85c0-a142-44ef-9522-ff45bbb904b5',
    '4657c66b-f74e-4d0c-bab7-951789abff87',
    '194534d5-fffe-4029-8c2f-738b06772b4c'
  )
)
AND is_doubt = true;
```

Then re-check `/confidence` to confirm `needs_review == 0`.

### Step 3c: Trigger Excel generation
```
POST /api/cma-reports/{report_id}/generate
```
Save the returned `task_id`.

### Step 3d: Poll for generation completion
```
GET /api/tasks/{task_id}/status
```
Poll every 10 seconds. **MAX 30 polls** (5 minutes).

### Step 3e: Download the generated CMA
```
GET /api/cma-reports/{report_id}/download
```
Returns `{ "signed_url": "...", "expires_in": 60 }`.

Download the file from signed_url and save to:
```
C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\test-results\bcipl\BCIPL_CMA_output.xlsm
```

---

## PHASE 4: CMA Excel Verification (THE CRITICAL TEST)

This is the **most important phase**. Open the generated .xlsm file with openpyxl and verify its contents.

### Step 4a: Open and inspect structure
```python
import openpyxl
wb = openpyxl.load_workbook(
    "C:/Users/ASHUTOSH/OneDrive/Desktop/CMA project -2/DOCS/test-results/bcipl/BCIPL_CMA_output.xlsm",
    keep_vba=True,
    data_only=True,
)
```

Log:
- All sheet names in the workbook
- Confirm "INPUT SHEET" exists
- Confirm .xlsm format (macros preserved)

### Step 4b: Verify headers (INPUT SHEET)
Read and log:
- **Row 7, Col A**: Client name (should be "BCIPL")
- **Row 8, Cols B-H**: Years (should be 2021, 2022, 2023, 2024, 2025, 2026, 2027)
- **Row 10, Cols B-D**: Nature (should be "audited", "audited", "audited")
- **Row 10, Cols E-H**: Nature (should be "Projected")

### Step 4c: Verify P&L data rows (rows 17–109)
Scan INPUT SHEET rows 17-109, columns B (FY2021), C (FY2022), D (FY2023).

For each cell that has a non-zero value:
- Log: `Row {row} | Col {col_letter} (FY{year}) | Value: {value} | CMA Field: {field_name}`
- Look up the field name from this mapping:

Key P&L rows to check:
```
Row 22: Domestic Sales
Row 23: Export Sales
Row 41: Raw Materials Consumed (Imported)
Row 42: Raw Materials Consumed (Indigenous)
Row 45: Wages
Row 48: Power, Coal, Fuel and Water
Row 67: Salary and staff expenses
Row 83: Interest on Fixed Loans / Term loans
Row 99: Income Tax provision
```

### Step 4d: Verify Balance Sheet data rows (rows 111–262)
Same scan for BS rows 111-262, columns B-D.

Key BS rows to check:
```
Row 116: Issued, Subscribed and Paid up (Share Capital)
Row 131: Working Capital Bank Finance - Bank 1
Row 162: Gross Block
Row 163: Less Accumulated Depreciation
Row 194: Raw Material Indigenous
Row 201: Finished Goods
Row 206: Domestic Receivables
Row 213: Bank Balances
Row 242: Sundry Creditors for goods
```

### Step 4e: CRITICAL — FY2022 unit conversion check
FY2022 (Column C) values should be in lakhs WITHOUT double-conversion.

**Sanity check**: Compare FY2021 (Col B) and FY2023 (Col D) values with FY2022 (Col C) for key rows.
- FY2021 and FY2023 are in rupees ÷ 100,000 = lakhs
- FY2022 is already in lakhs ÷ 1 = lakhs
- All three columns should be in the SAME order of magnitude (lakhs)

**RED FLAG**: If FY2022 values are 100,000x smaller than FY2021/FY2023, the per-document conversion is broken.
**RED FLAG**: If FY2022 values are 100,000x larger than FY2021/FY2023, it's being multiplied instead of divided.

### Step 4f: Count populated cells
```
Total cells with data in P&L section (rows 17-109, cols B-D): ___
Total cells with data in BS section (rows 111-262, cols B-D): ___
Total populated cells: ___
Empty cells that should have data: ___
```

### Step 4g: Formula preservation check
Scan for cells in rows 17-262 that contain formulas (start with "=").
Log any formulas found — they should be preserved from the template (subtotals, totals).
Confirm NO formulas were overwritten with raw values.

### CMA Excel Gates

| Check | Expected | Gate |
|-------|----------|------|
| INPUT SHEET exists | Yes | HARD |
| Row 7 = "BCIPL" | Yes | HARD |
| Row 8 years correct (2021-2027) | Yes | HARD |
| P&L section has data (>= 5 rows populated) | Yes | HARD |
| BS section has data (>= 5 rows populated) | Yes | HARD |
| FY2022 values same order of magnitude as FY2021/2023 | Yes | HARD (unit conversion) |
| Formulas preserved | Yes | HARD |
| Total populated cells >= 20 | Yes | SOFT |

---

## PHASE 5: Browser Test (Playwright)

Test the frontend UI flow at http://localhost:3002. Use the Playwright MCP tools.

### Step 5a: Login bypass
Navigate to `http://localhost:3002/clients`. Auth is disabled, should load directly.

### Step 5b: Navigate to BCIPL
Click on the "BCIPL" client in the client list.

### Step 5c: Verify document list
Confirm 3 documents are visible:
- FY2021: BCIPL_ Final Accounts_2020-21.xls
- FY2022: BCIPL_ Final Accounts_2021-22.xls
- FY2023: BCIPL_ FY 2023 Final Accounts_25092023.xls

Take a screenshot.

### Step 5d: Check extraction status badges
All 3 should show status badges. After Phase 1, they should be "verified" or "extracted".

### Step 5e: Navigate to CMA report
If a CMA report exists for BCIPL, click into it. Verify:
- Confidence summary is visible (high/medium/needs_review counts)
- Classification table loads
- Items show descriptions (NOT "(no description)")
- Doubt items show proper doubt reasons (NOT "AI classification unavailable")

Take a screenshot of the classification view.

### Step 5f: Check doubt resolution page
If doubts exist, navigate to the doubts page. Verify:
- Each doubt shows the line item description
- Each doubt shows the doubt reason
- CMA field selector dropdown works
- No "(no description)" text visible

Take a screenshot.

### Browser Test Gates

| Check | Expected | Gate |
|-------|----------|------|
| Client page loads | Yes | HARD |
| Documents visible | 3 documents | HARD |
| No "(no description)" in UI | 0 occurrences | HARD |
| No "AI classification unavailable" in doubt reasons | 0 occurrences | HARD |
| Screenshots captured | >= 3 | SOFT |

---

## PHASE 6: Final Report

Save comprehensive report to:
```
C:\Users\ASHUTOSH\OneDrive\Desktop\CMA project -2\DOCS\test-results\bcipl\TEST_REPORT.md
```

The report MUST include ALL of the following:

### 1. Extraction Results
| Document | FY | Items | Source Unit | Sections | Status | Time |
|----------|-----|-------|------------|----------|--------|------|

### 2. Sheet Filter Audit (per document)
- Sheets included vs excluded
- Any false positives/negatives

### 3. Sample Extracted Items (10 per document, 30 total)
| FY | Description | Amount | Section |
|----|-------------|--------|---------|

### 4. Classification Results
| Metric | Value |
|--------|-------|
| Total items | |
| High confidence (>= 0.8) | |
| Medium confidence (0.5-0.8) | |
| Doubts | |
| AI failures (unavailable) | |
| Null descriptions | |
| Fuzzy matches | |
| AI matches | |

### 5. Classification Samples
- 10 best high-confidence matches
- 10 doubt items with reasons

### 6. CMA Excel Verification
| Check | Result | Details |
|-------|--------|---------|
| INPUT SHEET exists | | |
| Client name = BCIPL | | |
| Years in Row 8 | | |
| P&L rows populated | | |
| BS rows populated | | |
| FY2022 unit conversion correct | | |
| Formulas preserved | | |
| Total populated cells | | |

### 7. FY2022 Unit Conversion Deep Check
| Row | CMA Field | FY2021 (B) | FY2022 (C) | FY2023 (D) | Same magnitude? |
|-----|-----------|------------|------------|------------|-----------------|
(Fill for at least 5 key rows like Domestic Sales, Share Capital, Gross Block)

### 8. Browser Test Results
| Test | Result | Screenshot |
|------|--------|------------|
| Client page | | |
| Document list | | |
| Classification view | | |
| Doubt resolution | | |
| No "(no description)" | | |

### 9. Overall Verdict
```
PASS / FAIL / PARTIAL
```
With a detailed paragraph explaining what worked, what failed, and any issues found.

---

## Error Taxonomy (use in report)

| Type | Name | Description |
|------|------|-------------|
| A | Synonym Miss | Same thing, different name |
| B | Industry Context | Industry changes the mapping |
| C | Conditional | Amount/context determines field |
| D | Aggregation | Sub-items need netting |
| E | Correct Doubt | AI rightly flagged uncertainty |
| F | Correct Ambiguity | Genuinely needs human judgment |
| G | AI Failure | API error, no tool call, malformed response |
| H | Extraction Error | Wrong amount, wrong description, wrong sheet |
| I | Unit Error | Wrong conversion, double-conversion, missing conversion |

---

## HARD STOPS (stop immediately if any occur)

1. **Cost guard**: Classification API calls are handled by the backend worker — no direct API calls from this prompt
2. **Infinite loop**: Never poll more than MAX specified per phase
3. **AI failure flood**: > 5 "AI classification unavailable" → STOP (Anthropic API broken)
4. **Zero items**: Any document extracts 0 items → STOP (extractor broken)
5. **Unit conversion broken**: FY2022 values 100,000x different from FY2021/FY2023 → STOP

When you hit a hard stop, save whatever results you have to the report and clearly state what failed and where.
